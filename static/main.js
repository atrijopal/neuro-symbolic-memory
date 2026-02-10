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
                edges: { color: "#343434", arrows: 'to', smooth: { type: 'cubicBezier' } },
                nodes: { shape: 'box', color: '#97C2FC', font: { color: '#343434' } },
                physics: { enabled: true, solver: 'forceAtlas2Based' }
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
        } catch (error)
            {
            console.error("Failed to fetch full graph:", error);
        }
    };

    const handleSend = async () => {
        const message = userInput.value.trim();
        if (!message) return;

        addMessageToChat(message, 'user');
        userInput.value = '';
        userInput.disabled = true;
        sendButton.disabled = true;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: message, session_id: sessionId })
            });

            if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);

            const result = await response.json();
            addMessageToChat(result.response, 'assistant');
            
            if (result.newly_extracted_graph) {
                updateGraphFromDelta(result.newly_extracted_graph);
            }

        } catch (error) {
            console.error('Error during chat:', error);
            addMessageToChat(`Sorry, I encountered an error: ${error.message}. Please try again.`, 'assistant');
        } finally {
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        }
    };

    const handleReset = async () => {
        if (!confirm("Are you sure you want to wipe all memory? This cannot be undone.")) return;
        
        try {
            const response = await fetch('/api/reset', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // FIX: The backend expects 'user_input', even for reset.
                body: JSON.stringify({ user_input: "reset", session_id: sessionId })
            });

            if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);

            if (network) {
                nodes.clear();
                edges.clear();
            }
            chatWindow.innerHTML = '';
            addMessageToChat('Memory has been wiped. Let\'s start over.', 'assistant');
        } catch (error) {
            console.error('Error resetting memory:', error);
            addMessageToChat(`Sorry, I could not reset the memory: ${error.message}.`, 'assistant');
        }
    };

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