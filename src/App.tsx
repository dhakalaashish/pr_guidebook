import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)

  useEffect(() => {
    // console.log("Effect is running");
    // console.log("Using API:", import.meta.env.VITE_API_URL);
    const fetchTime = async() => {
      try {
        const res = await fetch(`/api/time`);
        // const res = await fetch(`${import.meta.env.VITE_API_URL}/api/time`);
        const data = await res.json();
        console.log(data)
        setCurrentTime(data.time)
      } catch (err){
        console.error("Failed to fetch time", err)
      }
    }
    fetchTime()
  }, [])

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>The current time is {currentTime}.</p>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
