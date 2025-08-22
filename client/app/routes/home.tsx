import type { Route } from "./+types/home";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button"
import { useState, useEffect } from 'react'
// import { Welcome } from "../welcome/welcome";
import ChecklistDisplay from "~/components/ChecklistDisplay";
import ErrorMessage from "~/components/ErrorMessage";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export default function Home() {
  const [issueUrl, setIssueUrl] = useState("");
  const [prUrl, setPrUrl] = useState("");
  const [gettingStartedData, setGettingStartedData] = useState(null);
  const [implementationData, setImplementationData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const res1 = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/generate_guidebook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issueUrl }),
      });
      const issueInfo = await res1.json();

      if (!res1.ok) {
        setError("Failed to fetch issue details.");
        return;
      }

      // Step 2: Call getting_started_guide API using issueInfo
      const res2 = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/getting_started_guide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(issueInfo),
      });
      const getting_started = await res2.json();

      if (!res2.ok) {
        setError("Failed to generate getting started guide.");
        return;
      }
      setGettingStartedData(getting_started);
      
      // Step 3: Implementation guide (steps + tests)
      const res3 = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/implementation_guide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...issueInfo, suggestion_level: 3 }), // default function-level detail
      });
      const implementation_guide = await res3.json();
      if (!res3.ok) {
        setError("Failed to generate implementation guide.");
        return;
      }
      setImplementationData(implementation_guide);

      setError("");
    } catch (err) {
      setError("Failed to fetch checklist.");
    } finally {
      setLoading(false)
    }
  };

  const handleRefresh = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prUrl }),
      });
      const json = await res.json();
      setData(json);
      setError("");
    } catch (err) {
      setError("Failed to refresh checklist.");
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Get Step-by-Step Guidelines To Complete Your Pull Request</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            placeholder="Paste GitHub Issue URL"
            value={issueUrl}
            onChange={(e) => setIssueUrl(e.target.value)}
          />
          <Button onClick={handleGenerate}>
            {loading ? "Generating..." : "Generate Guidebook"}
          </Button>
        </CardContent>
      </Card>

      {/* A. Getting Started */}
      {gettingStartedData && (
        <>
          <Card  className="mt-6">
            <CardHeader>
              <CardTitle>A. Getting Started</CardTitle>
            </CardHeader>
            <CardContent>
              <ChecklistDisplay data={gettingStartedData} />
            </CardContent>
          </Card>
        </>
      )}

      {implementationData && (
        <>
          <Card  className="mt-6">
            <CardHeader>
              <CardTitle>B. Implementation</CardTitle>
            </CardHeader>
            <CardContent>
              <ChecklistDisplay data={implementationData} />
              <div className="mt-4 space-y-2">
                <Input
                  placeholder="Paste PR branch URL to refresh checklist"
                  value={prUrl}
                  onChange={(e) => setPrUrl(e.target.value)}
                />
                <Button onClick={handleRefresh}>Automated Review</Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {error && <ErrorMessage message={error} />}
    </div>
  );
}
