import FileUpload from './components/file_upload';
import ChatInterface from './components/chat_interface';

export default function Home() {
  return (
    <main className="home-container">
      <header className="home-header">
        <h1 className="home-title">JuraGen: AI Legal Drafting Assistant</h1>
      </header>

      <section className="home-section">
        <FileUpload />
      </section>

      <div className="home-divider"></div>

      <section className="home-section">
        <ChatInterface />
      </section>
    </main>
  );
}
