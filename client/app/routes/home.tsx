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
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/generate_guidebook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issueUrl }),
      });
      const json = await res.json();
      setData(json);
      setError("");
    } catch (err) {
      setError("Failed to fetch checklist.");
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
          <Button onClick={handleGenerate}>Generate Guidebook</Button>
        </CardContent>
      </Card>

      {data && (
        <>
          <ChecklistDisplay data={data} />
          <Card>
            <CardContent className="space-y-4 pt-6">
              <Input
                placeholder="Paste PR branch URL to refresh checklist"
                value={prUrl}
                onChange={(e) => setPrUrl(e.target.value)}
              />
              <Button onClick={handleRefresh}>Refresh Checklist</Button>
            </CardContent>
          </Card>
        </>
      )}

      {error && <ErrorMessage message={error} />}
    </div>
  );
}
