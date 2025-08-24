import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "~/components/ui/accordion";
import { useState } from "react";

export default function ChecklistDisplay({ data }) {
  const renderValue = (value) => {
    if (!value) return null;
    if (typeof value === "string") return <span>{value}</span>;
    if (Array.isArray(value)) {
      return (
        <ul className="space-y-1 ml-4 list-disc">
          {value.map((v, i) => (
            <li key={i}>{typeof v === "object" ? JSON.stringify(v) : v}</li>
          ))}
        </ul>
      );
    }
    if (typeof value === "object") {
      return (
        <ul className="space-y-1 ml-4 list-disc">
          {Object.entries(value).map(([k, v], i) => (
            <li key={i}>
              <strong>{k.replace(/_/g, " ")}:</strong> {renderValue(v)}
            </li>
          ))}
        </ul>
      );
    }
    return <span>{String(value)}</span>;
  };

  return (
    <Accordion type="multiple" className="w-full mt-4">
      {Object.entries(data).map(([title, description], index) => (
        <AccordionItem key={index} value={`item-${index}`}>
          <AccordionTrigger>{title.replace(/_/g, " ")}</AccordionTrigger>
          <AccordionContent className="pt-2">
            {renderValue(description)}
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
