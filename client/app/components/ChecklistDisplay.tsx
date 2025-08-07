import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "~/components/ui/accordion";

export default function ChecklistDisplay({ data }) {
  return (
    <Accordion type="multiple" className="w-full mt-4">
      {Object.entries(data).map(([title, description], index) => (
        <AccordionItem key={index} value={`item-${index}`}>
          <AccordionTrigger>{title}</AccordionTrigger>
          <AccordionContent>
            <p className="mb-2 text-sm text-muted-foreground whitespace-pre-line">
              {description}
            </p>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
