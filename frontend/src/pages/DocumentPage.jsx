import React, { useState, useEffect } from 'react';
// --- FIX 1: Import useNavigate ---
import { Link, useNavigate } from 'react-router-dom';
// --- FIX 2: Remove the duplicate import ---
import { getDocuments, uploadDocument } from '../services/api'; 
import '../App.css';

function DocumentPage() {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  // Call the useNavigate hook
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch documents when the component loads
    const fetchDocuments = async () => {
      try {
        const response = await getDocuments();
        setDocuments(response.data);
      } catch (err) {
        setError('Failed to fetch documents.');
        console.error(err);
      }
    };
    fetchDocuments();
  }, []);

  const handleFileChange = (e) => {
    // Reset error when a new file is selected
    setError('');
    setSelectedFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload.');
      return;
    }
    setUploading(true);
    setError('');
    try {
      const response = await uploadDocument(selectedFile);
      // Add the new document to the top of the list
      setDocuments([response.data, ...documents]);
      // Clear the file input after successful upload
      document.querySelector('input[type="file"]').value = "";
      setSelectedFile(null);
    } catch (err) {
      setError('File upload failed. Please try again.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    navigate('/');
  };

  return (
    <div className="doc-page-container">
      <header className="app-header">
        <Link to="/chat">Back to Chat</Link>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>
      <main className="doc-main-content">
        <h1>My Documents</h1>
        <div className="upload-section card">
          <h3>Upload New PDF</h3>
          <input type="file" accept=".pdf" onChange={handleFileChange} />
          <button onClick={handleUpload} disabled={!selectedFile || uploading}>
            {uploading ? 'Uploading...' : 'Upload Document'}
          </button>
          {error && <p className="error-message">{error}</p>}
        </div>
        <div className="document-list card">
          <h3>Uploaded Documents</h3>
          {documents.length > 0 ? (
            <ul className="doc-ul">
              {documents.map(doc => (
                <li key={doc.id} className="doc-li">
                  <span>&#128442; {doc.original_filename}</span>
                  <span className={`status status-${doc.ingestion_status.toLowerCase()}`}>
                    {doc.ingestion_status}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p>You haven't uploaded any documents yet.</p>
          )}
        </div>
      </main>
    </div>
  );
}

export default DocumentPage;