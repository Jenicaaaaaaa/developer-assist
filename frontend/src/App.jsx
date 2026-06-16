import { useState } from 'react'
import axios from 'axios'
import './App.css'

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [command, setCommand] = useState('ask')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessages([...messages, { role: 'user', content: input }])
    setInput('')

    try {
      const res = await axios.post(`http://localhost:8000/api/${command}`, 
        command === 'ask' ? { question: input } : { error: input }
      )
      setMessages(m => [...m, { role: 'assistant', content: res.data.answer }])
    } catch (err) {
      setMessages(m => [...m, { role: 'assistant', content: 'Error: ' + err.message }])
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', flexDirection: 'column', background: '#1a1a1a', color: '#e0e0e0' }}>
      <header style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', padding: '2rem', color: 'white', textAlign: 'center' }}>
        <h1>DevAssist</h1>
      </header>
      <div style={{ display: 'flex', flex: 1, gap: '1rem', padding: '1rem' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#252525', borderRadius: '8px' }}>
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {messages.map((m, i) => <div key={i} style={{ background: m.role === 'user' ? '#667eea' : '#404040', padding: '1rem', borderRadius: '8px', maxWidth: '70%', alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start' }}>{m.content}</div>)}
          </div>
          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', padding: '1rem', borderTop: '1px solid #404040' }}>
            <input type="text" value={input} onChange={e => setInput(e.target.value)} placeholder="Ask something..." style={{ flex: 1, padding: '0.75rem', background: '#1a1a1a', color: '#e0e0e0', border: '1px solid #404040', borderRadius: '4px' }} />
            <button type="submit" style={{ padding: '0.75rem 2rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Send</button>
          </form>
        </div>
        <aside style={{ width: '180px', background: '#252525', padding: '1.5rem', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {['ask', 'debug', 'review', 'diff', 'commit', 'summary'].map(cmd => <button key={cmd} onClick={() => setCommand(cmd)} style={{ padding: '0.75rem', background: command === cmd ? '#667eea' : '#404040', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', textTransform: 'capitalize' }}>{cmd}</button>)}
        </aside>
      </div>
    </div>
  )
}