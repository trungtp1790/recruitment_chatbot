"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type JobItem = {
  id: string;
  title: string;
  company: string;
  location: string;
  salary_min?: number;
  salary_max?: number;
  apply_url?: string;
};

type MemorySlot = {
  industries: string[];
  locations: string[];
  salary_min: number | null;
};

type ChatResponse = {
  session_id: string;
  reply: string;
  jobs: JobItem[];
  intent: string;
  memory_updated: MemorySlot;
};

const INTENT_LABELS: Record<string, string> = {
  find_job: "Tìm việc",
  off_topic: "Ngoài phạm vi",
  bot_identity: "Giới thiệu bot"
};

type Message = { role: "user" | "bot"; content: string };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const GREETING_MESSAGE = "Tôi có thể giúp được gì cho bạn? Chúng ta nên bắt đầu từ đâu?";

export default function HomePage() {
  const [sessionId, setSessionId] = useState("web-pending");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", content: GREETING_MESSAGE }
  ]);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastIntent, setLastIntent] = useState<string | null>(null);
  const [memory, setMemory] = useState<MemorySlot | null>(null);

  const canSend = useMemo(() => message.trim().length > 0 && !loading, [message, loading]);

  useEffect(() => {
    setSessionId(`web-${Math.random().toString(36).slice(2, 10)}`);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSend) return;
    const payload = { session_id: sessionId, message };
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = (await response.json()) as ChatResponse;
      setMessages((prev) => [...prev, { role: "bot", content: data.reply }]);
      setJobs(data.jobs || []);
      setLastIntent(data.intent ?? null);
      setMemory(data.memory_updated ?? null);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content:
            "Không gọi được backend API. Vui lòng kiểm tra lại backend container, database và cấu hình môi trường."
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <header className="header">
        <span className="badge">Học tập · Demo mentor · Mở rộng thực tế</span>
        <h1 className="title">Recruitment Chatbot</h1>
        <p className="subtitle">
          Trợ lý tìm việc bằng tiếng Việt. Phiên làm việc: <strong>{sessionId}</strong>
        </p>
        <p className="doc-hint">
          API tài liệu:{" "}
          <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">
            Swagger /health
          </a>
        </p>
      </header>

      <div className="grid">
        <section className="card chat-card">
          <div className="messages">
            {messages.map((m, idx) => (
              <div key={idx} className={`bubble ${m.role}`}>
                <strong>{m.role === "user" ? "Bạn" : "Chatbot"}:</strong> {m.content}
              </div>
            ))}
          </div>

          <form onSubmit={onSubmit} className="input-row">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ví dụ: Tìm việc kế toán ở Hà Nội, lương từ 15 triệu"
              className="input"
            />
            <button type="submit" disabled={!canSend} className="button">
              {loading ? "Đang gửi..." : "Gửi"}
            </button>
          </form>
        </section>

        <section className="card side-stack">
          {lastIntent ? (
            <div className="intent-row">
              <span className="intent-label">Intent (demo):</span>
              <span className={`intent-pill intent-${lastIntent}`}>
                {INTENT_LABELS[lastIntent] ?? lastIntent}
              </span>
            </div>
          ) : null}

          {memory ? (
            <div className="memory-panel">
              <h3 className="memory-title">Bộ nhớ phiên (Redis slot)</h3>
              <ul className="memory-list">
                <li>
                  <span className="memory-k">Ngành:</span>{" "}
                  {memory.industries.length ? memory.industries.join(", ") : "—"}
                </li>
                <li>
                  <span className="memory-k">Địa điểm:</span>{" "}
                  {memory.locations.length ? memory.locations.join(", ") : "—"}
                </li>
                <li>
                  <span className="memory-k">Lương tối thiểu:</span>{" "}
                  {memory.salary_min != null
                    ? `${memory.salary_min.toLocaleString("vi-VN")} VND`
                    : "—"}
                </li>
              </ul>
            </div>
          ) : null}

          <h2 className="jobs-title">Việc làm gợi ý</h2>
          {jobs.length === 0 ? (
            <p className="empty">Chưa có kết quả phù hợp.</p>
          ) : (
            <div className="job-list">
              {jobs.map((job) => (
                <article key={job.id} className="job-item">
                  <div className="job-title">{job.title}</div>
                  <div className="job-meta">{job.company}</div>
                  <div className="job-meta">Địa điểm: {job.location}</div>
                  <div className="job-meta">
                    Mức lương: {job.salary_min?.toLocaleString("vi-VN") ?? 0} -{" "}
                    {job.salary_max?.toLocaleString("vi-VN") ?? 0} VND
                  </div>
                  {job.apply_url ? (
                    <a href={job.apply_url} target="_blank" rel="noreferrer" className="job-link">
                      Xem tin tuyển dụng
                    </a>
                  ) : (
                    <span className="job-link-demo">Ứng tuyển: dữ liệu demo (chưa gắn URL thật)</span>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
