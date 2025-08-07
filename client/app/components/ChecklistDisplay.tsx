import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "~/components/ui/accordion";
import { useState } from "react";

export default function ChecklistDisplay({ data }) {
  return (
    <Accordion type="multiple" className="w-full mt-4">
      {Object.entries(data).map(([title, description], index) => {
        const items = description.split("\n").filter(Boolean);
        return (
          <AccordionItem key={index} value={`item-${index}`}>
            <AccordionTrigger>{title}</AccordionTrigger>
            <AccordionContent>
              <ul className="space-y-1">
                {items.map((item, i) => (
                  <CheckboxItem key={i} label={item} />
                ))}
              </ul>
            </AccordionContent>
          </AccordionItem>
        );
      })}
    </Accordion>
  );
}

function CheckboxItem({ label }) {
  const [checked, setChecked] = useState(false);
  return (
    <li className="flex items-center space-x-2">
      <input
        type="checkbox"
        className="h-4 w-4"
        checked={checked}
        onChange={() => setChecked(!checked)}
      />
      <span className={checked ? "line-through text-muted-foreground" : ""}>
        {label}
      </span>
    </li>
  );
}
