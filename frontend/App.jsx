const { useState, useEffect, useRef } = React;

function PixelBlastBackground() {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let time = 0;
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', resize);
    resize();
    
    const render = () => {
      time += 0.02;
      ctx.fillStyle = '#050505'; 
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      const pixelSize = 25;
      ctx.fillStyle = 'rgba(245, 245, 220, 0.12)'; 
      
      for (let y = 0; y < canvas.height; y += pixelSize) {
        for (let x = 0; x < canvas.width; x += pixelSize) {
          const dx = x - canvas.width / 2;
          const dy = y - canvas.height / 2;
          const dist = Math.sqrt(dx*dx + dy*dy);
          
          const wave = Math.sin(dist * 0.005 - time) * 0.5 + 0.5;
          const size = wave * (pixelSize * 0.7);
          
          if (size > 1) {
            ctx.fillRect(x + (pixelSize-size)/2, y + (pixelSize-size)/2, size, size);
          }
        }
      }
      animationFrameId = requestAnimationFrame(render);
    };
    render();
    
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} style={{ position: 'fixed', top: 0, left: 0, zIndex: -1, pointerEvents: 'none' }} />;
}

function ClickSparkProvider({ children }) {
  const [sparks, setSparks] = useState([]);

  const handleClick = (e) => {
    const id = Date.now();
    const x = e.clientX;
    const y = e.clientY;
    setSparks(prev => [...prev, { id, x, y }]);
    setTimeout(() => {
      setSparks(prev => prev.filter(s => s.id !== id));
    }, 400);
  };

  return (
    <div onClick={handleClick} style={{ minHeight: '100vh', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      {children}
      {sparks.map(s => (
        <div key={s.id} className="spark-burst" style={{ left: s.x, top: s.y }}>
          {Array.from({length: 8}).map((_, i) => (
            <div key={i} className="spark-wrapper" style={{ transform: `rotate(${i * 45}deg)` }}>
              <div className="spark-line" />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function App() {
  const [formData, setFormData] = useState({
    Store: '',
    Item: '',
    OnPromotion: '',
    Date: '',
    UnitPrice: ''
  });

  const [loading, setLoading] = useState(false);
  const [predictionUnits, setPredictionUnits] = useState(null);
  const [predictionRevenue, setPredictionRevenue] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    let parsedValue = value;
    
    if (value === '') {
      parsedValue = '';
    } else if (name === 'OnPromotion') {
      parsedValue = value === 'true';
    } else if (type === 'number') {
      parsedValue = Number(value);
    }
    
    setFormData((prev) => ({
      ...prev,
      [name]: parsedValue
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setPredictionUnits(null);
    setPredictionRevenue(null);

    try {
      // The /api route is proxied to the deployed Render backend via vercel.json.
      // If resolving locally, make sure to use localhost port 8000 directly
      // or set up a local proxy mirroring this!
      const API_URL = window.location.hostname === "localhost" 
          ? 'http://127.0.0.1:8000/predict' 
          : '/api/predict';

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Prediction request failed. Is the backend running?');
      }

      const data = await response.json();
      setPredictionUnits(data.prediction_units);
      setPredictionRevenue(data.prediction_revenue);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ClickSparkProvider>
      <PixelBlastBackground />
      <div className="container">
        <div className="header">
          <h1>Demand Prophet</h1>
          <p>AI-Powered Sales & Revenue Forecasting</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="form-grid">
            
            <div className="input-group">
              <label htmlFor="Store">Store Number</label>
              <input type="number" id="Store" name="Store" value={formData.Store} onChange={handleChange} required min="1" placeholder="e.g. 1" />
            </div>

            <div className="input-group">
              <label htmlFor="Item">Item Number</label>
              <input type="number" id="Item" name="Item" value={formData.Item} onChange={handleChange} required min="1" placeholder="e.g. 1001" />
            </div>
            
            <div className="input-group">
              <label htmlFor="UnitPrice">Unit Price (₹)</label>
              <input type="number" step="0.01" id="UnitPrice" name="UnitPrice" value={formData.UnitPrice} onChange={handleChange} required placeholder="e.g. 199.99" />
            </div>

            <div className="input-group">
              <label htmlFor="OnPromotion">On Promotion?</label>
              <select id="OnPromotion" name="OnPromotion" value={formData.OnPromotion === '' ? '' : formData.OnPromotion.toString()} onChange={handleChange} required>
                <option value="" disabled hidden>Select</option>
                <option value="false">No</option>
                <option value="true">Yes</option>
              </select>
            </div>

            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label htmlFor="Date">Target Date</label>
              <input type="date" id="Date" name="Date" value={formData.Date} onChange={handleChange} required />
            </div>

            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? <span className="spinner"></span> : 'Predict Demand & Revenue'}
            </button>
          </form>

          {predictionUnits !== null && predictionRevenue !== null && (
            <div className="result-container" style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem', background: 'transparent', border: 'none', padding: 0 }}>
              
              <div style={{ background: 'var(--success-bg)', border: '1px solid var(--success-border)', padding: '1.5rem', borderRadius: '12px', width: '100%' }}>
                <div className="result-label">Demand Forecast</div>
                <div className="result-value">
                  We expect to sell {predictionUnits.toLocaleString('en-IN')} units.
                </div>
              </div>

              <div style={{ background: 'var(--success-bg)', border: '1px solid var(--success-border)', padding: '1.5rem', borderRadius: '12px', width: '100%' }}>
                <div className="result-label" style={{ color: '#E8E8D0' }}>Revenue Forecast</div>
                <div className="result-value" style={{ color: '#E8E8D0' }}>
                  This will generate ₹ {predictionRevenue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} in sales.
                </div>
              </div>

            </div>
          )}

          {error && (
            <div className="result-container error">
              <div className="result-label">Error</div>
              <div className="result-value">{error}</div>
            </div>
          )}
        </div>
      </div>
    </ClickSparkProvider>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
