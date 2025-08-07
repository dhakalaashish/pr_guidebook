export default function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="mt-4 p-3 bg-red-100 text-red-600 rounded-md text-sm font-medium">
      {message}
    </div>
  );
}
