import React, { useState } from 'react'
import { Skeleton } from 'boneyard-js/react'

interface ArticleCardProps {
  title: string
  excerpt: string
  author: string
  date: string
}

const ArticleCard: React.FC<ArticleCardProps> = ({ title, excerpt, author, date }) => (
  <div className="card">
    <h2>{title}</h2>
    <p>{excerpt}</p>
    <div style={{ fontSize: '0.9rem', color: '#666' }}>
      {author} · {date}
    </div>
  </div>
)

const App: React.FC = () => {
  const [loading, setLoading] = useState(true)

  return (
    <div>
      <h1>Boneyard Smoke App</h1>
      
      <button onClick={() => setLoading(!loading)}>
        Toggle loading (current: {loading ? 'true' : 'false'})
      </button>

      <div style={{ marginTop: '2rem' }}>
        <h3>loading=true</h3>
        <Skeleton name="article-card" loading={loading} fixture={
          <ArticleCard 
            title="Sample Article Title" 
            excerpt="This is a sample excerpt for the article card component used in Boneyard skeleton testing."
            author="Test Author"
            date="2026-07-05"
          />
        } />

        <h3>loading=false</h3>
        <ArticleCard 
          title="Sample Article Title" 
          excerpt="This is a sample excerpt for the article card component used in Boneyard skeleton testing."
          author="Test Author"
          date="2026-07-05"
        />
      </div>
    </div>
  )
}

export default App
