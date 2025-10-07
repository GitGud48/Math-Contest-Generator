// pages/api/problems.js
import axios from 'axios';

const FLASK_API_URL = 'http://localhost:4000'; // Your Flask backend URL

export default async function handler(req, res) {
  try {
    const { database, limit = 20 } = req.query;
    
    // Forward request to Flask backend
    const response = await axios.get(`${FLASK_API_URL}/problems`, {
      params: { database, limit },
    });
    
    res.status(200).json(response.data);
  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ 
      error: 'Failed to fetch problems',
      details: error.message 
    });
  }
}
