document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const resetButton = document.getElementById('reset-button');
    const graphContainer = document.getElementById('knowledge-graph');

    let sessionId = localStorage.getItem('neuro_session_id') || `web-${Date.now()}`;
    localStorage.setItem('neuro_session_id', sessionId);

    // --- Graph Visualization (vis.js) ---
    let network = null;
    let nodes = null;
    let edges = null;

    const initializeGraph = () => {
        if (typeof vis === 'undefined') {
            console.error("vis.js library not loaded. Graph will not be displayed.");
            graphContainer.innerHTML = '<p style="color: red; text-align: center; padding: 20px;">Graph library (vis.js) failed to load. Check your internet connection or ad-blockers.</p>';
            return;
        }
        try {
            nodes = new vis.DataSet([]);
            edges = new vis.DataSet([]);
            const graphData = { nodes, edges };
            const graphOptions = {
                layout: { hierarchical: false },
                edges: {
                    color: "#848484",
                    arrows: { to: { enabled: true, scaleFactor: 0.5 } },
                    smooth: { type: 'continuous' }
                },
                nodes: {
                    shape: 'dot',
                    size: 15,
                    color: {
                        background: '#00C853',
                        border: '#005522',
                        highlight: { background: '#69F0AE', border: '#00C853' }
                    },
                    font: { color: '#333', size: 14, face: 'Inter, sans-serif' },
                    borderWidth: 2
                },
                physics: {
                    enabled: true,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {
                        gravitationalConstant: -50,
                        centralGravity: 0.01,
                        springLength: 100,
                        springConstant: 0.08,
                        damping: 0.4,
                        avoidOverlap: 0.5
                    },
                    stabilization: {
                        enabled: true,
                        iterations: 1000,
                        updateInterval: 25,
                        onlyDynamicEdges: false,
                        fit: true
                    },
                    minVelocity: 0.75
                },
                interaction: { hover: true }
            };
            network = new vis.Network(graphContainer, graphData, graphOptions);
        } catch (error) {
            console.error("Failed to initialize vis.js network:", error);
            graphContainer.innerHTML = '<p style="color: red; text-align: center; padding: 20px;">Error initializing knowledge graph.</p>';
        }
    };

    const addMessageToChat = (text, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.textContent = text;
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };

    const updateGraphFromDelta = (graphDelta) => {
        if (!network || !graphDelta || !graphDelta.nodes || !graphDelta.edges) return;
        try {
            const newNodes = graphDelta.nodes.map(n => ({ id: n.id, label: n.id }));
            const newEdges = graphDelta.edges.map(e => ({ from: e.src, to: e.dst, label: e.relation }));
            nodes.update(newNodes);
            edges.update(newEdges);
        } catch (error) {
            console.error("Failed to update graph:", error);
        }
    };

    const fetchFullGraph = async () => {
        if (!network) return;
        try {
            const response = await fetch(`/api/graph/${sessionId}`);
            const fullGraph = await response.json();
            nodes.clear();
            edges.clear();
            nodes.add(fullGraph.nodes);
            edges.add(fullGraph.edges);
        } catch (error) {
            console.error("Failed to fetch full graph:", error);
        }
    };

    const inspector = document.getElementById('memory-inspector');

    const updateInspector = (data) => {
        if (!data) return;
        // Format as per Hackathon requirement
        const output = {
            "active_memories": data.memories_used || [],
            "response_generated": true,
            "latency_ms": data.latency_ms || "unknown"
        };
        inspector.textContent = JSON.stringify(output, null, 2);
    };

    const handleSend = async () => {
        const message = userInput.value.trim();
        if (!message) return;

        addMessageToChat(message, 'user');
        userInput.value = '';
        userInput.disabled = true;
        sendButton.disabled = true;
        inspector.textContent = "Create Inference...";

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: message, session_id: sessionId })
            });

            if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);

            const result = await response.json();
            addMessageToChat(result.response, 'assistant');
            updateInspector(result);

            // Trigger an immediate graph refresh after response
            setTimeout(fetchFullGraph, 1000);

        } catch (error) {
            console.error('Error during chat:', error);
            addMessageToChat(`Sorry, I encountered an error: ${error.message}. Please try again.`, 'assistant');
        } finally {
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        }
    };

    // --- Auto-Refresh Graph (Heartbeat) ---
    // Poll every 3 seconds to show background extraction updates (Slow Pipe)
    setInterval(fetchFullGraph, 3000);

    // --- Initialize ---
    initializeGraph();

    sendButton.addEventListener('click', handleSend);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleSend();
    });
    resetButton.addEventListener('click', handleReset);

    addMessageToChat('Hello! I can remember facts you tell me. How can I help?', 'assistant');
    fetchFullGraph();
});