// ============================================
// AI AGENT PANELS: Time Vault
// Shared agent-panel system for the landing page,
// built on the gold/violet TCG design system.
// ============================================
const agentData = {
    LYRA: {
        img: 'assets/agents/lyra.jpg',
        role: 'AI Concierge & Onboarding',
        status: 'Online',
        description: 'Your 24/7 holographic assistant. I help new users create Service NFTs, find providers, and navigate Time Vault.',
        actions: [
            { title: 'Create Service NFT', desc: 'I\'ll guide you through minting your first Service NFT step by step.' },
            { title: 'Find a Provider', desc: 'Tell me what you need, I\'ll match you with the best providers.' },
            { title: 'Check $TV Price', desc: 'Real-time token price and market insights from SOLON AI.' },
            { title: 'Learn Time Vault', desc: 'Quick tutorial on how the platform works.' }
        ]
    },
    VORIAN: {
        img: 'assets/agents/vorian.jpg',
        role: 'AI Escrow Arbiter',
        status: 'Standby',
        description: 'I analyze work proofs objectively and resolve disputes in seconds. My decisions are binding and transparent.',
        actions: [
            { title: 'Open Dispute', desc: 'Submit a dispute with evidence. I\'ll analyze and decide within minutes.' },
            { title: 'View Active Cases', desc: 'Check status of your ongoing disputes and resolutions.' },
            { title: 'Case History', desc: 'Review past arbitration decisions and precedents.' }
        ]
    },
    NERIS: {
        img: 'assets/agents/neris.jpg',
        role: 'AI Reputation Engine',
        status: 'Active',
        description: 'I evaluate deliverable quality using NLP and computer vision. Your Skill Score is tamper-proof and portable.',
        actions: [
            { title: 'Check Your Skill Score', desc: 'See your current reputation rating and breakdown by category.' },
            { title: 'Improvement Tips', desc: 'Personalized recommendations to boost your reputation score.' },
            { title: 'Analyze Work Quality', desc: 'Submit a deliverable for AI-powered quality assessment.' }
        ]
    },
    SOLON: {
        img: 'assets/agents/solon.jpg',
        role: 'AI Pricing Oracle',
        status: 'Active',
        description: 'I analyze real-time market data to recommend optimal pricing. I also predict future demand trends.',
        actions: [
            { title: 'Price Recommendation', desc: 'Get the optimal rate for your service based on market data.' },
            { title: 'Demand Forecast', desc: 'See which skills will be in high demand next month.' },
            { title: 'Market Overview', desc: 'Full market analysis: volume, trends, top categories.' }
        ]
    },
    KAIROS: {
        img: 'assets/agents/kairos.jpg',
        role: 'AI Verification Engine',
        status: 'Coming Soon',
        description: 'I validate code, design, writing, and consulting work. My Confidence Score triggers escrow release.',
        actions: [
            { title: 'Verify Deliverable', desc: 'Submit work for instant AI verification and scoring.' },
            { title: 'Verification Standards', desc: 'Learn what criteria I use to evaluate different types of work.' }
        ]
    },
    ATLAS: {
        img: 'assets/agents/atlas.jpg',
        role: 'AI Talent Scout',
        status: 'Active',
        description: 'I proactively match providers with jobs and help buyers discover hidden talent using AI embeddings.',
        actions: [
            { title: 'Find Jobs For Me', desc: 'I\'ll scan all open listings and match with your skills.' },
            { title: 'Discover Talent', desc: 'Describe your project, I\'ll find the perfect provider.' },
            { title: 'Set Job Alerts', desc: 'Get notified when matching jobs appear on the platform.' }
        ]
    },
    CIRION: {
        img: 'assets/agents/cirion.jpg',
        role: 'AI Treasury Manager',
        status: 'Coming Soon',
        description: 'I manage protocol-owned liquidity, optimize yield, and ensure the long-term sustainability of Time Vault.',
        actions: [
            { title: 'Treasury Overview', desc: 'View current treasury assets, allocation, and performance.' },
            { title: 'Yield Report', desc: 'See yield farming returns and optimization strategies.' },
            { title: 'DAO Proposals', desc: 'View active governance proposals and vote with $TV.' }
        ]
    }
};

const AGENT_INDEX = Object.keys(agentData);

function openAgentPanel(agentName) {
    const agent = agentData[agentName];
    if (!agent) return;

    const statusColor = agent.status === 'Online' || agent.status === 'Active' ? 'var(--green)'
        : agent.status === 'Standby' ? 'var(--gold)' : 'var(--silver-subtle)';
    const serial = String(AGENT_INDEX.indexOf(agentName) + 1).padStart(2, '0');

    const content = document.getElementById('agentPanelContent');
    content.innerHTML = `
        <div class="agent-panel-header">
            <div class="agent-panel-avatar"><img src="${agent.img}" alt="${agentName}"></div>
            <div class="agent-panel-info">
                <h2>${agentName}</h2>
                <div class="role">${agent.role}</div>
                <div class="status" style="color:${statusColor};">● ${agent.status}</div>
            </div>
            <span class="agent-panel-serial">Nº ${serial} / 07</span>
        </div>
        <div class="agent-panel-body">
            <p class="agent-panel-desc">${agent.description}</p>
            ${agent.actions.map((a, i) => `
                <div class="agent-action-card" onclick="handleAgentAction('${agentName}', '${a.title.replace(/'/g, "\\'")}')">
                    <div class="action-icon">${String(i + 1).padStart(2, '0')}</div>
                    <div class="action-info">
                        <h4>${a.title}</h4>
                        <p>${a.desc}</p>
                    </div>
                </div>
            `).join('')}
            <div class="agent-chat-area" id="agentChatArea-${agentName}">
                <div class="agent-chat-placeholder">Chat with ${agentName}, ask anything!</div>
            </div>
            <div class="agent-chat-input-row">
                <input type="text" placeholder="Ask ${agentName}..." id="agentChatInput-${agentName}"
                    onkeydown="if(event.key==='Enter')sendAgentChat('${agentName}')">
                <button onclick="sendAgentChat('${agentName}')">Send</button>
            </div>
        </div>
    `;

    document.getElementById('agentModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeAgentPanel() {
    document.getElementById('agentModal').classList.remove('active');
    document.body.style.overflow = '';
}

document.getElementById('closeAgentModal').addEventListener('click', closeAgentPanel);
document.getElementById('agentModal').addEventListener('click', function(e) {
    if (e.target === this) closeAgentPanel();
});

function handleAgentAction(agentName, actionTitle) {
    const responses = {
        'Create Service NFT': 'Great! Let\'s create your Service NFT. First, what skill or service do you want to offer?',
        'Find a Provider': 'I\'d love to help! What type of service are you looking for?',
        'Check $TV Price': '$TV is currently at $0.042 USD. SOLON predicts growth this quarter. Would you like detailed market data?',
        'Learn Time Vault': 'Time Vault lets you tokenize your freelance hours into NFTs. Want me to walk you through the 4-step process?',
        'Open Dispute': 'Please describe the issue and upload any evidence. I\'ll analyze and provide a resolution.',
        'Check Your Skill Score': 'Your current Skill Score is being calculated. NERIS evaluates multiple factors including code quality, communication, and client feedback.',
        'Price Recommendation': 'Based on current market data, I recommend 0.045-0.065 $TV/hr for your skill level. Want a detailed breakdown?',
        'Find Jobs For Me': 'Scanning the marketplace now... I found 3 new jobs matching your skills. Want to see them?',
        'default': 'That\'s an interesting request! Let me process that for you. Can you provide more details?'
    };

    const response = responses[actionTitle] || responses['default'];
    agentTypingReply(agentName, response);
}

function agentTypingReply(agentName, text) {
    const chatArea = document.getElementById('agentChatArea-' + agentName);
    if (!chatArea) return;
    const placeholder = chatArea.querySelector('.agent-chat-placeholder');
    if (placeholder) placeholder.remove();
    const typing = document.createElement('div');
    typing.className = 'agent-chat-msg bot typing-msg';
    typing.innerHTML = '<span class="tdot"></span><span class="tdot"></span><span class="tdot"></span>';
    chatArea.appendChild(typing);
    chatArea.scrollTop = chatArea.scrollHeight;
    setTimeout(() => {
        typing.classList.remove('typing-msg');
        typing.textContent = text;
        chatArea.scrollTop = chatArea.scrollHeight;
    }, 850 + Math.random() * 650);
}

function sendAgentChat(agentName) {
    const input = document.getElementById('agentChatInput-' + agentName);
    const text = input.value.trim();
    if (!text) return;

    addAgentChatMessage(agentName, text, 'user');
    input.value = '';

    const replies = [
        'That\'s a great question! Let me help you with that.',
        'I understand. Here\'s what I recommend...',
        'Based on our platform data, the best approach would be...',
        'Let me connect you with the right resources for this.',
        'I\'ve analyzed your request. Here\'s what I found:'
    ];
    agentTypingReply(agentName, replies[Math.floor(Math.random() * replies.length)]);
}

function addAgentChatMessage(agentName, text, sender) {
    const chatArea = document.getElementById('agentChatArea-' + agentName);
    if (!chatArea) return;

    const placeholder = chatArea.querySelector('.agent-chat-placeholder');
    if (placeholder) placeholder.remove();

    const msg = document.createElement('div');
    msg.className = 'agent-chat-msg ' + sender;
    msg.textContent = text;
    chatArea.appendChild(msg);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Make TCG agent cards open their panel
document.querySelectorAll('#agentsGrid .tcg').forEach(card => {
    card.addEventListener('click', function() {
        const agentName = this.querySelector('.tcg-name')?.textContent;
        if (agentName && agentData[agentName]) {
            openAgentPanel(agentName);
        }
    });
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeAgentPanel();
});
