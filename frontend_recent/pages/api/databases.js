// pages/api/databases.js
import axios from 'axios';

const FLASK_API_URL = 'http://localhost:4000';

export default async function handler(req, res) {
  try {
    const response = await axios.get(`${FLASK_API_URL}/databases`);
    res.status(200).json(response.data);
  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ 
      error: 'Failed to fetch databases',
      details: error.message 
    });
  }
}
