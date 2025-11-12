import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar, Pie } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const API_BASE = 'http://localhost:8000';

function App() {
  const [userId, setUserId] = useState(1);
  const [riskScore, setRiskScore] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [chartData, setChartData] = useState({ labels: [], datasets: [] });

  useEffect(() => {
    fetchRiskScore();
    fetchAuditLogs();
  }, [userId]);

  const fetchRiskScore = async () => {
    try {
      const response = await axios.get(`${API_BASE}/risk-scores/${userId}`);
      setRiskScore(response.data);
    } catch (error) {
      console.error('Error fetching risk score:', error);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/audit-logs/?user_id=${userId}`);
      setAuditLogs(response.data);
      updateChart(response.data);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
  };

  const updateChart = (logs) => {
    const actions = logs.map(log => log.action);
    const counts = actions.reduce((acc, action) => {
      acc[action] = (acc[action] || 0) + 1;
      return acc;
    }, {});
    setChartData({
      labels: Object.keys(counts),
      datasets: [{
        label: 'Actions',
        data: Object.values(counts),
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    });
  };

  const captureBehavior = async (action, details) => {
    try {
      await axios.post(`${API_BASE}/behaviors/`, { user_id: userId, action, details });
      fetchAuditLogs();
      fetchRiskScore();
    } catch (error) {
      console.error('Error capturing behavior:', error);
    }
  };

  const simulateAttacker = async () => {
    try {
      await axios.post(`${API_BASE}/simulate-attacker/`, { user_id: userId });
      fetchAuditLogs();
      fetchRiskScore();
    } catch (error) {
      console.error('Error simulating attacker:', error);
    }
  };

  return (
    <div className="container">
      <h1>GuardAI Cybersecurity Dashboard</h1>
      <div className="dashboard">
        <div className="card">
          <h2>User Selection</h2>
          <input
            type="number"
            value={userId}
            onChange={(e) => setUserId(parseInt(e.target.value))}
            placeholder="User ID"
          />
        </div>
        <div className="card">
          <h2>Risk Score</h2>
          {riskScore ? (
            <div>
              <p>Score: {riskScore.score.toFixed(2)}</p>
              <p>Level: {riskScore.level}</p>
            </div>
          ) : (
            <p>Loading...</p>
          )}
        </div>
        <div className="card">
          <h2>Behavior Capture</h2>
          <button onClick={() => captureBehavior('login', 'User logged in')}>Simulate Login</button>
          <button onClick={() => captureBehavior('click', 'User clicked button')}>Simulate Click</button>
          <button onClick={() => captureBehavior('data_access', 'Accessed sensitive data')}>Simulate Data Access</button>
        </div>
        <div className="card">
          <h2>Simulated Attacker</h2>
          <button onClick={simulateAttacker}>Run Attacker Simulation</button>
        </div>
      </div>
      <div className="dashboard">
        <div className="card">
          <h2>Action Distribution</h2>
          <Bar data={chartData} />
        </div>
        <div className="card">
          <h2>Audit Logs</h2>
          <ul>
            {auditLogs.slice(0, 10).map(log => (
              <li key={log.id}>
                {log.action} - {new Date(log.timestamp).toLocaleString()} - Hash: {log.hash.substring(0, 10)}...
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;
