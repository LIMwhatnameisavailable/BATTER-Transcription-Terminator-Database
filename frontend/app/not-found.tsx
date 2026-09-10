import { ErrorState } from "@/components/PageFrame";

export default function NotFound() {
  return <ErrorState message="The requested BTED record was not found in the selected release." />;
}
