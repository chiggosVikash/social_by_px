import { ApprovalList } from "@/components/ApprovalList";

export default function ApprovalsPage() {

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Pending Approvals</h1>
      </div>

      <ApprovalList />
    </div>
  );
}
