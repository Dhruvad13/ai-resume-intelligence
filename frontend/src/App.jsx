import { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [role, setRole] = useState("backend");

  const uploadResume = async () => {
    if (!file) return alert("Upload resume");

    const form = new FormData();
    form.append("file", file);
    form.append("role", role);

    const res = await fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      body: form,
    });

    const data = await res.json();
    setResult(data);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white shadow-xl rounded-2xl p-8 w-full max-w-xl">
        <h2 className="text-2xl font-semibold text-gray-700 mb-6">
          AI Resume Intelligence
        </h2>

        <label className="block text-gray-600 mb-2">Job Role</label>
        <select
          className="w-full p-2 border rounded-xl mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          value={role}
          onChange={e => setRole(e.target.value)}
        >
          <option value="backend">Backend Developer</option>
          <option value="frontend">Frontend Developer</option>
          <option value="ml">ML Engineer</option>
        </select>

        <input
          type="file"
          className="w-full mb-4"
          onChange={e => setFile(e.target.files[0])}
        />

        <button
          onClick={uploadResume}
          className="w-full bg-indigo-500 text-white py-2 rounded-xl hover:bg-indigo-600 transition"
        >
          Analyze Resume
        </button>

        {result && (
          <div className="mt-6 space-y-3">
            <p className="text-lg font-medium">
              {result.selected ? "✅ Shortlisted" : "❌ Rejected"}
            </p>

            <p>Matching Score: <b>{result.score}%</b></p>

            <p><b>Skills Found:</b> {result.skills_found.join(", ")}</p>
            <p><b>Missing Skills:</b> {result.missing_skills.join(", ")}</p>

            <div>
              <p className="font-medium">Interview Questions</p>
              <ul className="list-disc pl-5">
                {result.interview_questions.map((q,i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>

            <div>
              <p className="font-medium">Resume Improvement Tips</p>
              <ul className="list-disc pl-5">
                {result.resume_suggestions.map((s,i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
