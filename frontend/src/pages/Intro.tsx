import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { users } from "../api/client";
import { ColorModeToggle } from "../components/ColorModeToggle";

/**
 * Welcome / intro screen — Feature 0 from the PRD.
 * Shown once after first login. "Let's get to work" dismisses,
 * marks intro_seen on the server, and routes to home.
 *
 * Copy is the team-approved intro that introduces Atlas (the system),
 * lays out the three funds, names the privacy enforcement model, and
 * lists the three-person team plus the system-role vs functional-role
 * distinction.
 */
export default function Intro() {
  const navigate = useNavigate();
  const [dismissing, setDismissing] = useState(false);

  const dismiss = async () => {
    setDismissing(true);
    try {
      await users.markIntroSeen();
    } catch {
      // Even if the server call fails, route to home — the worst case
      // is they see the intro again next session, not a broken app.
    }
    navigate("/", { replace: true });
  };

  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-brand-slate-900">
      <header className="flex items-center justify-end p-3">
        <ColorModeToggle />
      </header>

      <main className="flex flex-1 flex-col items-center px-6 py-8">
        <div className="w-full max-w-2xl">
          <div className="text-center">
            <h1 className="font-display text-4xl font-bold tracking-wide text-brand-slate-900 dark:text-brand-slate-50">
              Atlas
            </h1>
          </div>

          <h1 className="mt-10 text-center">Welcome to Atlas.</h1>

          <div className="mt-8 space-y-4 text-base leading-relaxed">
            <p>I&apos;m Atlas, the the team Team System.</p>

            <p>
              This is where we work — and what we&apos;re building here matters.
            </p>

            <p>
              the team — the the team — exists to find and fund the
              best of American manufacturing and energy, right now, for what
              this country needs most. That means three things. We serve
              immediate defense needs. We rebuild America&apos;s capacity to
              produce what is needed to defend America and her allies. And by
              2040, we displace China as the world&apos;s dominant industrial
              power.
            </p>

            <p>
              We run three funds. Region A. Region B. Energy. Each one
              targets a gap that matters — gaps that, if left unfilled, leave
              this country exposed.
            </p>

            <p>
              This tool is how we stay aligned, move fast, and stay focused on
              what matters.
            </p>

            <p>
              Privacy in Atlas is enforced at the database layer, not the UI.
              The UI surfaces these rules visually; it never substitutes for
              them. Every query is filtered by{" "}
              <code className="font-mono text-sm">current_user_id</code> before
              results are returned.
            </p>
          </div>

          <h2 className="mt-10 text-center text-sm font-bold uppercase tracking-wide">
            Three-person team
          </h2>

          <div className="mt-4 overflow-hidden rounded border border-brand-slate-900/20 dark:border-brand-slate-50/20">
            <table className="w-full text-sm">
              <thead className="bg-brand-slate-900/5 dark:bg-brand-slate-50/5">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold">Name</th>
                  <th className="px-3 py-2 text-left font-semibold">
                    System role
                  </th>
                  <th className="px-3 py-2 text-left font-semibold">
                    Functional role
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-brand-slate-900/10 dark:border-brand-slate-50/10">
                  <td className="px-3 py-2">Sarah Chen</td>
                  <td className="px-3 py-2">admin</td>
                  <td className="px-3 py-2">
                    AI Tools and Fund Partner, Atlas System Admin
                  </td>
                </tr>
                <tr className="border-t border-brand-slate-900/10 dark:border-brand-slate-50/10">
                  <td className="px-3 py-2">Priya Chang</td>
                  <td className="px-3 py-2">member</td>
                  <td className="px-3 py-2">
                    Fund Strategy, Industry Lead and Fund Partner
                  </td>
                </tr>
                <tr className="border-t border-brand-slate-900/10 dark:border-brand-slate-50/10">
                  <td className="px-3 py-2">Maya Patel Richmond</td>
                  <td className="px-3 py-2">member</td>
                  <td className="px-3 py-2">
                    Investor Relations, Government Relations Lead and Fund
                    Partner
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-sm leading-relaxed">
            System role gates technical access — admin can reach{" "}
            <code className="font-mono">/admin/audit</code> and (Phase 2+)
            approve cross-team change requests. Functional role describes what
            the person does and surfaces in Atlas&apos;s conversational copy.
          </p>

          <div className="mt-12 text-center">
            <button
              type="button"
              onClick={dismiss}
              disabled={dismissing}
              className="inline-flex h-12 items-center justify-center rounded bg-brand-red-600 px-10 text-sm font-bold uppercase tracking-wide text-white hover:bg-brand-red-400 focus:outline-none focus:ring-2 focus:ring-brand-amber-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {dismissing ? "…" : "Let's get to work"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
