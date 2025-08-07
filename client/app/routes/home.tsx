import type { Route } from "./+types/home";
import { Button } from "~/components/ui/button"
// import { Welcome } from "../welcome/welcome";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export default function Home() {

  // const [issueUrl, setIssueUrl] = useState("");
  // const [prUrl, setPrUrl] = useState("");
  // const [data, setData] = useState(null);
  // const [error, setError] = useState("");

  // const handleGenerate = async () => {
  //   try {
  //     const res = await fetch("/api/generate", {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify({ issueUrl }),
  //     });
  //     const json = await res.json();
  //     setData(json);
  //     setError("");
  //   } catch (err) {
  //     setError("Failed to fetch checklist.");
  //   }
  // };

  // const handleRefresh = async () => {
  //   try {
  //     const res = await fetch("/api/refresh", {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify({ prUrl }),
  //     });
  //     const json = await res.json();
  //     setData(json);
  //     setError("");
  //   } catch (err) {
  //     setError("Failed to refresh checklist.");
  //   }
  // };

  return (
    <div className="flex min-h-svh flex-col items-center justify-center">
      <Button>Click me</Button>
    </div>
  )
}
