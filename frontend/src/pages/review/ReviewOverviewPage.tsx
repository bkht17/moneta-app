import { Navigate, useParams } from "react-router";

import OverviewView from "../../components/OverviewView";
import { ErrorList } from "../../components/ui/Notice";
import Spinner from "../../components/ui/Spinner";
import { apiErrors } from "../../lib/api";
import { useOverview } from "../../lib/queries";

export default function ReviewOverviewPage() {
  const { id } = useParams();
  const overview = useOverview(id);

  if (overview.isPending) return <Spinner label="Calculating your overview" />;
  if (overview.isError) {
    const errors = apiErrors(overview.error);
    // Flags still open or intake not finished: the wizard shows what is missing.
    if (errors.some((e) => e.code === "unresolved_flags" || e.code === "intake_incomplete")) {
      return <Navigate to={`/reviews/${id}`} replace />;
    }
    return <ErrorList errors={errors} />;
  }
  return <OverviewView overview={overview.data} />;
}
