import type { Route } from "./+types/home";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "~/components/ui/accordion";
import { useState } from "react";
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
  const [gettingStartedData, setGettingStartedData] = useState<any>(null);
  const [implementationData, setImplementationData] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isUrl = (s?: string) => !!s && /^https?:\/\//i.test(s);

  const handleGenerate = async () => {
    setLoading(true);
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

      const res3 = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/implementation_guide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...issueInfo, suggestion_level: 3 }), // default: function-level detail
      });
      const implementation_guide = await res3.json();
      if (!res3.ok) {
        setError("Failed to generate implementation guide.");
        return;
      }
      setImplementationData(implementation_guide);

      setError("");
    } catch {
      setError("Failed to fetch checklist.");
    } finally {
      setLoading(false);
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
      setImplementationData(json);
      setError("");
    } catch {
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
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>A. Getting Started</CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" className="w-full mt-4">
              {/* 1) Possible Duplicates */}
              <AccordionItem value="gs-duplicates">
                <AccordionTrigger>Check for Duplicate Issues</AccordionTrigger>
                <AccordionContent className="space-y-3">
                  {Array.isArray(gettingStartedData.issue_duplicates) && gettingStartedData.issue_duplicates.length > 0 ? (
                    <ul className="space-y-2">
                      {gettingStartedData.issue_duplicates.map(
                        (d: { title: string; url: string; status?: string }, idx: number) => (
                          <li key={idx} className="flex items-start justify-between gap-3">
                            <a href={d.url} target="_blank" rel="noreferrer" className="underline underline-offset-2">
                              {d.title}
                            </a>
                            <span className="shrink-0 inline-block rounded-full border px-2 py-0.5 text-xs">
                              {d.status || "unknown"}
                            </span>
                          </li>
                        )
                      )}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">No obvious duplicates found.</p>
                  )}
                </AccordionContent>
              </AccordionItem>

              {/* 2) Feature Uniqueness */}
              <AccordionItem value="gs-uniqueness">
                <AccordionTrigger>Feature Uniqueness Guidance</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="inline-block rounded-full border px-2 py-0.5 text-xs">
                      {gettingStartedData?.feature_uniqueness?.status ?? "n/a"}
                    </span>
                  </div>
                  {gettingStartedData?.feature_uniqueness?.guidance && (
                    <p className="text-sm whitespace-pre-wrap">
                      {gettingStartedData.feature_uniqueness.guidance}
                    </p>
                  )}
                </AccordionContent>
              </AccordionItem>

              {/* 3) Alignment with Project Vision */}
              <AccordionItem value="gs-vision">
                <AccordionTrigger>Alignment with Project Vision</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  {gettingStartedData?.align_with_project_vision?.status === "no conflict" ? (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="inline-block rounded-full border px-2 py-0.5 text-xs">no conflict</span>
                      <span className="text-muted-foreground">This proposal aligns with the project’s vision.</span>
                    </div>
                  ) : gettingStartedData?.align_with_project_vision?.status === "conflict" ? (
                    <div className="space-y-2">
                      <p className="text-sm">
                        <strong>Conflict:</strong>{" "}
                        {gettingStartedData.align_with_project_vision.conflict_reason}
                      </p>
                      {Array.isArray(gettingStartedData.align_with_project_vision.suggested_alternatives) && (
                        <div className="text-sm">
                          <strong>Suggested alternatives:</strong>
                          <ul className="list-disc ml-5 mt-1">
                            {gettingStartedData.align_with_project_vision.suggested_alternatives.map(
                              (alt: string, i: number) => <li key={i}>{alt}</li>
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm whitespace-pre-wrap">
                      {typeof gettingStartedData?.align_with_project_vision === "string"
                        ? gettingStartedData.align_with_project_vision
                        : "No alignment info available."}
                    </p>
                  )}
                </AccordionContent>
              </AccordionItem>

              {/* 4) Contribution Must-Do's */}
              <AccordionItem value="gs-guidelines">
                <AccordionTrigger>Contribution Must-Do’s</AccordionTrigger>
                <AccordionContent className="space-y-4">
                  {/* CLA / Signing */}
                  <div className="space-y-1">
                    <h4 className="font-medium">Signing / CLA</h4>
                    {isUrl(gettingStartedData?.tune_contribution_guidelines?.signing_guidelines) ? (
                      <a
                        className="text-sm underline underline-offset-2"
                        href={gettingStartedData.tune_contribution_guidelines.signing_guidelines}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {gettingStartedData.tune_contribution_guidelines.signing_guidelines}
                      </a>
                    ) : (
                      <p className="text-sm">
                        {gettingStartedData?.tune_contribution_guidelines?.signing_guidelines || "not applicable"}
                      </p>
                    )}
                  </div>

                  {/* Local Setup */}
                  <div className="space-y-1">
                    <h4 className="font-medium">Local Setup Instructions</h4>
                    <pre className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                      {gettingStartedData?.tune_contribution_guidelines?.local_setup_instructions ||
                        "No setup instructions found."}
                    </pre>
                  </div>

                  {/* PR Creation */}
                  <div className="space-y-1">
                    <h4 className="font-medium">PR Creation Process</h4>
                    <pre className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                      {gettingStartedData?.tune_contribution_guidelines?.PR_creation_process ||
                        "No PR creation process found."}
                    </pre>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* 5) Scope / PR Plan */}
              <AccordionItem value="gs-scope">
                <AccordionTrigger>Scope & Suggested PR Plan</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="inline-block rounded-full border px-2 py-0.5 text-xs">
                      {gettingStartedData?.issue_scope?.status || "unknown"}
                    </span>
                  </div>

                  {Array.isArray(gettingStartedData?.issue_scope?.pr_plan) &&
                  gettingStartedData.issue_scope.pr_plan.length > 0 ? (
                    <ul className="space-y-2">
                      {gettingStartedData.issue_scope.pr_plan.map(
                        (pr: { title: string; description?: string }, i: number) => (
                          <li key={i} className="border rounded p-3">
                            <div className="font-medium">{pr.title}</div>
                            {pr.description && (
                              <div className="text-sm text-muted-foreground mt-1 whitespace-pre-wrap">
                                {pr.description}
                              </div>
                            )}
                          </li>
                        )
                      )}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      This appears manageable as a single PR.
                    </p>
                  )}
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      )}

      {/* B. Implementation */}
      {implementationData && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>B. Implementation</CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" className="w-full mt-4">
              {/* Steps */}
              <AccordionItem value="impl-steps">
                <AccordionTrigger>Steps to Implement</AccordionTrigger>
                <AccordionContent>
                  {Array.isArray(implementationData.steps) && implementationData.steps.length > 0 ? (
                    <ol className="list-decimal ml-5 space-y-1">
                      {implementationData.steps.map((s: string, i: number) => (
                        <li key={i} className="whitespace-pre-wrap">{s}</li>
                      ))}
                    </ol>
                  ) : (
                    <p className="text-sm text-muted-foreground">No steps generated.</p>
                  )}
                </AccordionContent>
              </AccordionItem>

              {/* Tests */}
              <AccordionItem value="impl-tests">
                <AccordionTrigger>Testing Instructions</AccordionTrigger>
                <AccordionContent>
                  {Array.isArray(implementationData.tests) && implementationData.tests.length > 0 ? (
                    <ol className="list-decimal ml-5 space-y-1">
                      {implementationData.tests.map((t: string, i: number) => (
                        <li key={i} className="whitespace-pre-wrap">{t}</li>
                      ))}
                    </ol>
                  ) : (
                    <p className="text-sm text-muted-foreground">No testing steps generated.</p>
                  )}
                </AccordionContent>
              </AccordionItem>
            </Accordion>

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
      )}

      {error && <ErrorMessage message={error} />}
    </div>
  );
}