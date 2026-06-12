import { ApprovalList, ApprovalItem } from "@/components/ApprovalList";

async function getPendingApprovals(): Promise<ApprovalItem[]> {
  // Mock fetch, replace with actual API call to FastAPI
  // e.g. await fetch(`${process.env.NEXT_PUBLIC_API_URL}/approvals/pending`, { cache: "no-store" })
  return [
    {
      id: 1,
      project_name: "Tech Startup Marketing",
      article_title: "AI is revolutionizing SaaS",
      slides: ["Slide 1 Content", "Slide 2 Content", "Slide 3 Content"]
    }
  ];
}

export default async function ApprovalsPage() {
  const items = await getPendingApprovals();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Pending Approvals</h1>
      </div>

      <ApprovalList initialItems={items} />
    </div>
  );
}
