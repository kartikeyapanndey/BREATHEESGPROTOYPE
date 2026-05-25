import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [currentView, setCurrentView] = useState<'upload' | 'dashboard'>('dashboard')
  const [records, setRecords] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  // A hardcoded tenant ID for the prototype
  const tenantId = '00000000-0000-0000-0000-000000000001'

  const fetchRecords = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/records/')
      if (res.ok) {
        const data = await res.json()
        setRecords(data)
      }
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    if (currentView === 'dashboard') {
      fetchRecords()
    }
  }, [currentView])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    const form = e.target as HTMLFormElement
    const fileInput = form.elements.namedItem('file') as HTMLInputElement
    const sourceInput = form.elements.namedItem('source_type') as HTMLSelectElement
    
    if (!fileInput.files?.length) return

    const formData = new FormData()
    formData.append('file', fileInput.files[0])
    formData.append('source_type', sourceInput.value)
    formData.append('tenant_id', tenantId)

    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/records/upload/', {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        alert('Upload successful')
        setCurrentView('dashboard')
      } else {
        const err = await res.json()
        alert(`Error: ${JSON.stringify(err)}`)
      }
    } catch (e) {
      console.error(e)
      alert('Upload failed')
    }
    setLoading(false)
  }

  const handleApprove = async (id: string, currentQty: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/records/${id}/approve/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: 'APPROVED',
          quantity: currentQty
        })
      })
      if (res.ok) {
        fetchRecords()
      }
    } catch (e) {
      console.error(e)
    }
  }

  const handleReject = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/records/${id}/approve/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: 'REJECTED'
        })
      })
      if (res.ok) {
        fetchRecords()
      }
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Breathe ESG</h1>
        <nav>
          <button 
            className={`nav-link ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
            style={{background: 'transparent', border: 'none', cursor: 'pointer'}}
          >
            Dashboard
          </button>
          <button 
            className={`nav-link ${currentView === 'upload' ? 'active' : ''}`}
            onClick={() => setCurrentView('upload')}
            style={{background: 'transparent', border: 'none', cursor: 'pointer'}}
          >
            Upload Data
          </button>
        </nav>
      </header>

      <main className="animate-fade-in">
        {currentView === 'upload' && (
          <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <h2 style={{marginTop: 0}}>Ingest Source Data</h2>
            <p style={{color: 'var(--text-secondary)'}}>Upload a CSV, TSV, or JSON file depending on the source type.</p>
            
            <form onSubmit={handleUpload} className="upload-form">
              <div className="form-group">
                <label>Source Type</label>
                <select name="source_type" required>
                  <option value="SAP_FLAT_FILE">SAP Fuel & Procurement (CSV/TSV)</option>
                  <option value="UTILITY_CSV">Utility Electricity (CSV)</option>
                  <option value="CONCUR_JSON">Concur Travel API Dump (JSON)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Data File</label>
                <input type="file" name="file" required />
              </div>

              <button type="submit" className="btn" disabled={loading}>
                {loading ? 'Processing...' : 'Upload & Parse'}
              </button>
            </form>
          </div>
        )}

        {currentView === 'dashboard' && (
          <div className="glass-panel">
            <h2 style={{marginTop: 0}}>Analyst Review Dashboard</h2>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Category</th>
                    <th>Date</th>
                    <th>Quantity</th>
                    <th>Unit</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {records.length === 0 && (
                    <tr>
                      <td colSpan={7} style={{textAlign: 'center', padding: '2rem'}}>
                        No records found. Go upload some data.
                      </td>
                    </tr>
                  )}
                  {records.map(r => (
                    <tr key={r.id}>
                      <td>
                        {r.source_type}
                        <br/>
                        <small style={{color: 'var(--text-secondary)'}}>{r.file_name}</small>
                      </td>
                      <td>{r.category.replace('_', ' ')}</td>
                      <td>{r.start_date || '-'}</td>
                      <td>
                        {r.status === 'PENDING_REVIEW' ? (
                           <input 
                              type="number" 
                              defaultValue={r.quantity || ''} 
                              id={`qty-${r.id}`}
                              style={{ width: '80px', padding: '0.25rem' }}
                           />
                        ) : (
                          r.quantity || '-'
                        )}
                      </td>
                      <td>{r.unit || '-'}</td>
                      <td>
                        <span className={`status-badge status-${r.status.toLowerCase().replace('_review', '')}`}>
                          {r.status}
                        </span>
                        {r.validation_errors && r.validation_errors.length > 0 && (
                          <div style={{marginTop: '0.5rem'}}>
                            {r.validation_errors.map((err: string, i: number) => (
                              <div key={i} className="error-pill">⚠️ {err}</div>
                            ))}
                          </div>
                        )}
                      </td>
                      <td>
                        {r.status === 'PENDING_REVIEW' && (
                          <div style={{display: 'flex', gap: '0.5rem'}}>
                            <button 
                              className="btn" 
                              style={{padding: '0.25rem 0.5rem'}}
                              onClick={() => {
                                const input = document.getElementById(`qty-${r.id}`) as HTMLInputElement;
                                handleApprove(r.id, input.value);
                              }}
                            >
                              Approve
                            </button>
                            <button 
                              className="btn btn-danger" 
                              style={{padding: '0.25rem 0.5rem'}}
                              onClick={() => handleReject(r.id)}
                            >
                              Reject
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
