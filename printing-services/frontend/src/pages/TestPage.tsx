import { useState } from 'react'

export default function TestPage() {
  const [count, setCount] = useState(0)
  
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>PrintMarket Test Page</h1>
      <p>If you see this, React is working!</p>
      <button onClick={() => setCount(count + 1)} style={{ padding: '10px', fontSize: '16px' }}>
        Clicked {count} times
      </button>
      <div style={{ marginTop: '20px' }}>
        <a href="/login" style={{ color: 'blue', textDecoration: 'underline' }}>Go to Login</a>
      </div>
    </div>
  )
}
