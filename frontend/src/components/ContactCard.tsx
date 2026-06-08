/**
 * Simple contact card + ContactCardList wrapper.
 *
 * Renders one row per contact returned by the search_contacts tool.
 * Owner-scoped privacy: cards owned by the caller get a quiet "yours"
 * badge; private contacts owned by someone else still show because the
 * backend's serialize step withholds nothing here (a fuller portal
 * would add a redaction layer — out of scope for this demo).
 */

import { Lock } from "lucide-react";
import type { ContactCardData, ExportFilter } from "../api/client";

interface CardProps {
  contact: ContactCardData;
}

function ContactCard({ contact }: CardProps) {
  return (
    <article className="rounded border border-brand-slate-700/30 bg-white p-3 shadow-sm dark:border-brand-slate-50/20 dark:bg-brand-slate-800">
      <header className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-brand-slate-900 dark:text-brand-slate-50">
            {contact.name}
          </h3>
          {contact.title || contact.company_name ? (
            <p className="text-xs text-brand-slate-700 dark:text-brand-slate-50/80">
              {[contact.title, contact.company_name].filter(Boolean).join(" · ")}
            </p>
          ) : null}
        </div>
        <div className="flex items-center gap-1.5">
          {contact.is_private ? (
            <span
              className="inline-flex items-center text-brand-slate-700/70 dark:text-brand-slate-50/60"
              title="Private contact"
            >
              <Lock size={12} />
            </span>
          ) : null}
          {contact.is_self_owned ? (
            <span
              className="rounded bg-brand-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-brand-amber-500"
              title="You own this contact"
            >
              Yours
            </span>
          ) : null}
        </div>
      </header>

      <dl className="mt-2 space-y-0.5 text-xs text-brand-slate-700 dark:text-brand-slate-50/80">
        {contact.email ? (
          <div>
            <dt className="sr-only">Email</dt>
            <dd>{contact.email}</dd>
          </div>
        ) : null}
        {contact.cell_phone ? (
          <div>
            <dt className="sr-only">Cell</dt>
            <dd>{contact.cell_phone}</dd>
          </div>
        ) : null}
        {contact.country ? (
          <div>
            <dt className="sr-only">Country</dt>
            <dd className="opacity-70">{contact.country}</dd>
          </div>
        ) : null}
      </dl>

      {contact.notes ? (
        <p className="mt-2 whitespace-pre-wrap text-xs italic text-brand-slate-700/80 dark:text-brand-slate-50/70">
          {contact.notes}
        </p>
      ) : null}
    </article>
  );
}

interface ListProps {
  contacts: ContactCardData[];
  truncated: boolean;
  limit: number;
  // Legacy props kept so existing call sites don't need to change shape.
  // Not actively used in this simplified card.
  showExGov?: boolean;
  exportFilter?: ExportFilter;
}

export function ContactCardList({ contacts, truncated, limit }: ListProps) {
  if (contacts.length === 0) {
    return <p className="text-xs italic opacity-70">No contacts matched.</p>;
  }
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {contacts.map((c) => (
          <ContactCard key={c.id} contact={c} />
        ))}
      </div>
      {truncated ? (
        <p className="text-[11px] italic opacity-70">
          Showing the first {limit}. Refine your search to narrow further.
        </p>
      ) : null}
    </div>
  );
}
