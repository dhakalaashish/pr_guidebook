import type { Route } from "./+types/home";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "~/components/ui/accordion";
import ReactMarkdown from "react-markdown"
import { useState } from "react";
import ErrorMessage from "~/components/ErrorMessage";

export function meta({ }: Route.MetaArgs) {
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
  const [automatedReviewData, setAutomatedReviewData] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [issueInfo, setIssueInfo] = useState<any>(null);

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
      setIssueInfo(issueInfo); // Store issue info for later use (needed for implementation guide)
      setError("");
    } catch {
      setError("Failed to generate guidebook.");
    } finally {
      setLoading(false);
    }
  };

  const handleImplementation = async (pr_title: string, pr_description: string) => {
    if (!issueInfo) {
      setError("Please generate the guidebook first.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/implementation_guide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...issueInfo, pr_title, pr_description, suggestion_level: 3 }), // default: function-level detail
      });

      const implementation_guide = await res.json();
      if (!res.ok) {
        setError("Failed to generate implementation guide.");
        return;
      }

      setImplementationData(implementation_guide);
      setError("");
    } catch {
      setError("Error generating implementation guide.");
    } finally {
      setLoading(false);
    }
  };

  const handleAutomateReview = async (prUrl: string) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_SERVER_URL}/api/automate_PR_review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...issueInfo, pr_url: prUrl, suggestion_level: 3 }), // default: function-level detail
      });
      const json = await res.json();
      setAutomatedReviewData(json);
      setError("");
    } catch {
      setError("Failed to refresh checklist.");
    }
  };

  // utils/parseImplementation.ts
  function parseImplementation(raw: string) {
    if (!raw) return [];

    // Remove ```json or ``` at start and ``` at end
    const cleaned = raw
      .replace(/^```json\s*/, "")
      .replace(/```$/, "")
      .trim();

    try {
      // Parse JSON
      const parsed = JSON.parse(JSON.stringify(JSON.parse(cleaned)));
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.error("Failed to parse implementation steps:", e);
      return [];
    }
  }



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
                    <p className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                      <ReactMarkdown>
                      {gettingStartedData.feature_uniqueness.guidance}
                      </ReactMarkdown>
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
                      <ReactMarkdown>
                        {gettingStartedData?.tune_contribution_guidelines?.local_setup_instructions ||
                          "No setup instructions found."}
                      </ReactMarkdown>
                    </pre>
                  </div>

                  {/* PR Creation */}
                  <div className="space-y-1">
                    <h4 className="font-medium">PR Creation Process</h4>
                    <pre className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                      <ReactMarkdown>
                        {gettingStartedData?.tune_contribution_guidelines?.PR_creation_process ||
                          "No PR creation process found."}
                      </ReactMarkdown>
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
                          <li key={i} className="border rounded p-3 flex flex-col gap-2">
                            <div className="font-medium">{pr.title}</div>
                            {pr.description && (
                              <div className="text-sm text-muted-foreground mt-1 whitespace-pre-wrap">
                                {pr.description}
                              </div>
                            )}
                            <Button
                              onClick={() =>
                                handleImplementation(pr.title, pr.description || "")
                              }
                              className="bg-blue-600 text-white rounded px-3 py-1 text-sm hover:bg-blue-700"
                            >
                              Create Pull Request
                            </Button>
                          </li>
                        )
                      )}
                    </ul>
                  ) : (
                    <div className="flex flex-col gap-2">
                      <p className="text-sm text-muted-foreground">
                        This appears manageable as a single PR.
                      </p>
                      <Button
                        onClick={() =>
                          handleImplementation(
                            "",
                            ""
                          )
                        }
                        className="bg-blue-600 text-white rounded px-3 py-1 text-sm hover:bg-blue-700"
                      >
                        Create Pull Request
                      </Button>
                    </div>
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
          <CardContent className="space-y-4">
            <Accordion type="multiple" className="w-full mt-4">
              {/* Steps */}
              <AccordionItem value="gs-steps">
                <AccordionTrigger>Steps to Implement</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <div className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                    {implementationData.steps && implementationData.steps.length > 0 ? (
                      implementationData.steps.map((step: string, idx: number) => (
                        <CardContent key={idx} className="space-y-1">
                          <div className="text-sm break-words whitespace-pre-wrap overflow-x-auto">
                            <ReactMarkdown>{step}</ReactMarkdown>
                          </div>
                        </CardContent>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No steps generated.</p>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Tests */}
              <AccordionItem value="gs-tests">
                <AccordionTrigger>Testing Instructions</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  <div className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                    {implementationData.tests && implementationData.tests.length > 0 ? (
                      implementationData.tests.map((test: string, idx: number) => (
                        <CardContent key={idx} className="space-y-1">
                          <div className="text-sm break-words whitespace-pre-wrap overflow-x-auto">
                            <ReactMarkdown>{test}</ReactMarkdown>
                          </div>
                        </CardContent>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No testing steps generated.</p>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>

            </Accordion>
          </CardContent>
          <CardContent className="space-y-4">
            <div className="mt-4 space-y-2">
              <Input
                placeholder="Paste PR URL to refresh checklist"
                value={prUrl}
                onChange={(e) => setPrUrl(e.target.value)}
              />
              <Button onClick={() => handleAutomateReview(prUrl)}>Generate Automated Review</Button>
            </div>
          </CardContent>
        </Card>
      )}
      {/* C. Automated PR Review */}
      {automatedReviewData && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>C. Automated PR Review</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Accordion type="multiple" className="w-full mt-4">
              {/* 1) Issue Resolution */}
              <AccordionItem value="review-issue-resolution">
                <AccordionTrigger>Does the PR resolve the planned scope?</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  {automatedReviewData.validate_pr_resolution ? (
                    <div className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                      <ReactMarkdown>
                        {automatedReviewData.validate_pr_resolution}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No feedback available.</p>
                  )}
                </AccordionContent>
              </AccordionItem>

              {/* 2) Contribution Guidelines */}
              <AccordionItem value="review-contribution-guidelines">
                <AccordionTrigger>Contribution Guidelines Adherence</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  {automatedReviewData.review.enforce_contribution_guidelines ? (
                    <div className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                      <ReactMarkdown>
                        {automatedReviewData.enforce_contribution_guidelines}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No feedback available.</p>
                  )}
                </AccordionContent>
              </AccordionItem>

              {/* 3) PR Description Clarity */}
              <AccordionItem value="review-pr-description">
                <AccordionTrigger>PR Description Quality</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  {automatedReviewData.clear_pr_description ? (
                    <div className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                      <ReactMarkdown>
                        {automatedReviewData.clear_pr_description}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No feedback available.</p>
                  )}
                </AccordionContent>
              </AccordionItem>

              {/* 4) Testing Recommendations */}
              <AccordionItem value="review-testing">
                <AccordionTrigger>Testing Recommendations</AccordionTrigger>
                <AccordionContent className="space-y-2">
                  {automatedReviewData.tests_presence ? (
                    <div className="whitespace-pre-wrap text-sm font-mono bg-muted/40 rounded p-3">
                      <ReactMarkdown>
                        {automatedReviewData.tests_presence}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No feedback available.</p>
                  )}
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      )}

      {error && <ErrorMessage message={error} />}
    </div>
  );
}