import React, { useEffect, useState } from "react";

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null;

function App() {
  // Which screen: 1 = setup, 2 = interview
  const [step, setStep] = useState(1);

  // Settings (screen 1)
  const [candidateName, setCandidateName] = useState("");
  const [role, setRole] = useState("Software Engineer");
  const [customRole, setCustomRole] = useState("");
  const [experience, setExperience] = useState("Fresher");
  const [style, setStyle] = useState("Supportive");
  const [maxQuestions, setMaxQuestions] = useState(25);
  const [useResume, setUseResume] = useState(false);
  const [resumeText, setResumeText] = useState("");

  // Interview state (screen 2)
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [interviewId, setInterviewId] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [answer, setAnswer] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [interviewDone, setInterviewDone] = useState(false);


  // Voice (browser STT)
  const [supportsVoice, setSupportsVoice] = useState(!!SpeechRecognition);
  const [recognition, setRecognition] = useState(null);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    if (!SpeechRecognition) {
      setSupportsVoice(false);
      return;
    }

    const rec = new SpeechRecognition();
    rec.lang = "en-US";
    rec.continuous = false;
    rec.interimResults = false;

    rec.onresult = (event) => {
      if (event.results && event.results[0]) {
        const text = event.results[0][0].transcript;
        setAnswer(text);
      }
    };

    rec.onerror = () => {
      setIsRecording(false);
    };

    rec.onend = () => {
      setIsRecording(false);
    };

    setRecognition(rec);
  }, []);

  const addMessage = (role, content) => {
    setConversation((prev) => [...prev, { role, content }]);
  };

  const speak = (text) => {
    if (!voiceEnabled) return;
    if (!window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
  };

  const handleStartInterview = async () => {
  // Clear old interview state
  setConversation([]);
  setFeedback(null);
  setInterviewId(null);
  setAnswer("");
  setInterviewDone(false);


  // 🔹 Move to Screen 2 immediately
  setStep(2);

  const displayRole =
    role === "Custom" && customRole ? customRole : role;

  // Greeting from interviewer (frontend only)
  const greeting = candidateName
    ? `Hi ${candidateName}, I'm your AI interviewer for the ${displayRole} role. Let's get started!`
    : `Hello! I'm your AI interviewer for the ${displayRole} role. Let's get started.`;

  // Now we are already on Screen 2, so user will SEE this bubble
  addMessage("assistant", greeting);
  speak(greeting);

  const body = {
    role,
    customRole: role === "Custom" ? customRole : "",
    experience,
    style,
    maxQuestions,
    resumeText: useResume ? resumeText : null,
  };

  try {
    setIsThinking(true);
    const res = await fetch("/start-interview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error("Failed to start interview");
    }
    const data = await res.json();

    setInterviewId(data.interviewId);

    // First question from backend (intro / role-aware)
    addMessage("assistant", data.question);
    speak(data.question);
  } catch (err) {
    console.error(err);
    alert("Error starting interview. Check backend is running.");
    // If something fails, go back to setup screen
    setStep(1);
  } finally {
    setIsThinking(false);
  }
};

  const sendAnswer = async (end = false) => {
    if (!interviewId) {
      alert("Start the interview first.");
      return;
    }
    if (!end && !answer.trim()) {
      alert("Please type or dictate an answer.");
      return;
    }

    const currentAnswer = answer.trim();
    if (currentAnswer) {
      addMessage("user", currentAnswer);
    }
    setAnswer("");

    try {
      setIsThinking(true);
      const res = await fetch("/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interviewId,
          answer: end ? null : currentAnswer,
          end,
        }),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to send answer");
      }
      const data = await res.json();

      // If server signals done but still provides a final assistant message, show it first
      // After receiving 'data' from /answer
if (data.done) {
  // If server returned a final assistant message, show it FIRST
  if (data.nextQuestion) {
    addMessage("assistant", data.nextQuestion);
    // speak it only if voice is enabled
    if (voiceEnabled) speak(data.nextQuestion);
  }
  // then set feedback if provided
  if (data.feedbackMarkdown) {
    setFeedback(data.feedbackMarkdown);
  }
} else if (data.nextQuestion) {
  // normal flow: show next question and speak it
  addMessage("assistant", data.nextQuestion);
  if (voiceEnabled) speak(data.nextQuestion);
}


    } catch (err) {
      console.error(err);
      alert("Error sending answer.");
    } finally {
      setIsThinking(false);
    }
  };

  const handleRecordToggle = () => {
    if (!supportsVoice || !recognition) return;
    if (isRecording) {
      recognition.stop();
    } else {
      setAnswer("");
      recognition.start();
      setIsRecording(true);
    }
  };

  const handleReset = () => {
    // Clear interview state and return to setup screen
    setInterviewId(null);
    setConversation([]);
    setFeedback(null);
    setAnswer("");
    setStep(1);
  };

  const handleEndInterview = async () => {
  if (!interviewId) {
    alert("Start the interview first.");
    return;
  }
  if (interviewDone) {
    alert("Interview already finished.");
    return;
  }

  // Show immediate local closing message (keeps UX snappy)
  const closing_msg = `${
    candidateName ? `Thank you for your time, ${candidateName}.` : "Thank you for your time."
  } This concludes the interview.`;
  addMessage("assistant", closing_msg);
  if (voiceEnabled) speak(closing_msg);

  try {
    setIsThinking(true);

    const res = await fetch("/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        interviewId,
        answer: null,
        end: true,
      }),
    });

    // Debug: log raw response and JSON for quick inspection
    console.log("End-interview HTTP status:", res.status, "headers:", [...res.headers]);
    const data = await res.json().catch((err) => {
      console.error("Failed to parse JSON from /answer:", err);
      return null;
    });
    console.log("End-interview response JSON:", data);

    // If backend returns a final assistant message that's different, show it too
    if (data && data.nextQuestion && data.nextQuestion !== closing_msg) {
      addMessage("assistant", data.nextQuestion);
      if (voiceEnabled) speak(data.nextQuestion);
    }

    // Show feedback if provided
    if (data && (data.feedbackMarkdown || data.feedback)) {
      // handle both possible keys just in case
      const feedbackText = data.feedbackMarkdown ?? data.feedback;
      setFeedback(feedbackText);
      console.log("Feedback set in UI:", feedbackText);
    } else {
      console.warn("No feedback found in response.");
      // Optionally set a placeholder so user knows something happened
      setFeedback((prev) => prev || "No feedback received from server.");
    }

    setInterviewDone(true);
  } catch (err) {
    console.error(err);
    alert("Error ending interview. Check backend logs and the browser console.");
  } finally {
    setIsThinking(false);
  }
};


  // ---------- SCREEN 1: SETUP ----------
  if (step === 1) {
    return (
      <div className="app setup-screen">
        <div className="setup-content">
          <h1>🤖 AI Interview Practice Partner</h1>
          <p>
            🎯 Configure your mock interview and start practicing with a
            voice-enabled AI interviewer.
          </p>

          <label>
            Your name 
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              placeholder="name"
            />
          </label>

          <label>
  Target role
  <select
    value={role}
    onChange={(e) => setRole(e.target.value)}
  >
    <option value="Software Engineer">Software Engineer</option>
    <option value="Data Analyst">Data Analyst</option>
    <option value="Sales Associate">Sales Associate</option>
    <option value="Retail Associate">Retail Associate</option>
    <option value="Business Analyst">Business Analyst</option>
    <option value="Custom">Custom Role</option>
  </select>
</label>

{role === "Custom" && (
  <label>
    Enter custom role
    <input
      type="text"
      value={customRole}
      onChange={(e) => setCustomRole(e.target.value)}
      placeholder="e.g., AI Research Intern, Cloud Engineer..."
    />
  </label>
)}

          <label>
            Experience
            <select
              value={experience}
              onChange={(e) => setExperience(e.target.value)}
            >
              <option>Fresher</option>
              <option>0–2 years</option>
              <option>2–5 years</option>
              <option>Senior (5+ years)</option>
            </select>
          </label>

          <label>
            Interviewer style
            <select
              value={style}
              onChange={(e) => setStyle(e.target.value)}
            >
              <option>Supportive</option>
              <option>Strict</option>
            </select>
          </label>

          

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={useResume}
              onChange={(e) => setUseResume(e.target.checked)}
            />
            Use my resume for questions
          </label>

          {useResume && (
            <label>
              Paste your resume text
              <textarea
                rows={5}
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste your resume content here (summary, education, projects, skills)..."
              />
            </label>
          )}

          <button className="primary full-width" onClick={handleStartInterview}>
            🚀 Start interview
          </button>
        </div>
      </div>
    );
  }

  // ---------- SCREEN 2: INTERVIEW ----------
  return (
    <div className="app interview-layout">
      <main className="main">
        <div className="top-bar">
          <div className="top-bar-left">
            <button className="secondary" onClick={handleReset}>
              🔁 Reset interview
            </button>
            <button onClick={() => handleEndInterview()}>
              ⏹ End interview
            </button>

          </div>
          <div className="top-bar-right">
            <label className="inline-toggle">
              <input
                type="checkbox"
                checked={voiceEnabled}
                onChange={(e) => setVoiceEnabled(e.target.checked)}
              />
              Play interviewer questions as voice
            </label>
          </div>
        </div>

        <section className="conversation-section">
          <h2>Conversation</h2>
          {conversation.length === 0 && (
            <p className="info">Click "Reset interview" to go back or answer to continue.</p>
          )}

          <div className="conversation">
            {conversation.map((msg, idx) => (
              <div
                key={idx}
                className={
                  msg.role === "assistant"
                    ? "bubble assistant"
                    : "bubble user"
                }
              >
                <div className="bubble-role">
                  {msg.role === "assistant" ? "Interviewer" : "You"}
                </div>
                <div>{msg.content}</div>
              </div>
            ))}
            {isThinking && (
              <div className="bubble assistant">
                <div className="bubble-role">Interviewer</div>
                <div>Thinking…</div>
              </div>
            )}
          </div>
        </section>

        <section className="answer-section">
          <h2>Your answer</h2>
          <div className="answer-tabs">
            <div className="answer-column">
              <h3>✍️ Type answer</h3>
              <textarea
                rows={4}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Write or dictate your answer here..."
              />
              <button onClick={() => sendAnswer(false)}>
                Send text answer
              </button>
            </div>

            <div className="answer-column">
              <h3>🎙️ Voice answer</h3>
              {supportsVoice ? (
                <>
                  <p>
                    Click record and speak your answer. When you stop, the text
                    will appear in the box on the left. You can edit it before
                    sending.
                  </p>
                  <button onClick={handleRecordToggle}>
                    {isRecording ? "⏹ Stop recording" : "🎤 Start recording"}
                  </button>
                </>
              ) : (
                <p className="warning">
                  Voice recognition not supported in this browser.
                </p>
              )}
            </div>
          </div>
        </section>
      </main>

      <aside className="rightbar">
        <h2>📋 Interview Summary</h2>
        <p>
          <strong>Role:</strong>{" "}
          {role === "Custom" && customRole ? customRole : role}
        </p>
        <p>
          <strong>Experience:</strong> {experience}
        </p>
        <p>
          <strong>Style:</strong> {style}
        </p>
        

        <hr />
        <h2>🧾 Feedback</h2>
        {feedback ? (
          <div className="feedback">
            {feedback.split("\n").map((line, idx) => (
              <p key={idx}>{line}</p>
            ))}
          </div>
        ) : (
          <p className="info">
            Feedback will appear here after you click "Show feedback".
          </p>
        )}
      </aside>
    </div>
  );
}

export default App;
