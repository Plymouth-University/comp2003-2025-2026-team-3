import { el } from "../shared/lib/dom.js";

export function AccountPage(): HTMLElement {
  const wrap = el("div", { className: "bg-white rounded-xl shadow p-8 border border-slate-200" });

  //two-column layout -- left panel shows account info, right panel shows profile icon
  const contentWrap = el("div", { className: "grid grid-cols-3 gap-8" });

  //left column - account information
  const leftColumn = el("div", { className: "col-span-2 space-y-8" });

  //General section
  const generalSection = el("div", { className: "space-y-4" });
  generalSection.append(
    el("h3", { className: "text-lg font-bold text-slate-900", text: "General" })
  );

  const generalAttrs = [
    { label: "Name", value: "John Smith" },
    { label: "Date of Birth", value: "March 15, 1990" },
    { label: "Gender", value: "Male" },
  ];

  for (const attr of generalAttrs) {
    generalSection.append(
      el("div", { className: "space-y-1" }, [
        el("div", { className: "text-xs font-semibold text-slate-600 uppercase", text: attr.label }),
        el("div", { className: "text-sm text-slate-900", text: attr.value }),
      ])
    );
  }
  leftColumn.append(generalSection);

  //divider
  leftColumn.append(el("div", { className: "border-t border-slate-200" }));

  //Contact Information section
  const contactSection = el("div", { className: "space-y-4" });
  contactSection.append(
    el("h3", { className: "text-lg font-bold text-slate-900", text: "Contact Information" })
  );

  const contactAttrs = [
    { label: "Mobile Number", value: "+1 (555) 123-4567" },
    { label: "Office Phone", value: "+1 (555) 987-6543" },
    { label: "Personal Email", value: "john.smith@personal.com" },
    { label: "Work Email", value: "john.smith@global4.com" },
    { label: "Address", value: "123 Main Street, Suite 100, New York, NY 10001" },
  ];

  for (const attr of contactAttrs) {
    contactSection.append(
      el("div", { className: "space-y-1" }, [
        el("div", { className: "text-xs font-semibold text-slate-600 uppercase", text: attr.label }),
        el("div", { className: "text-sm text-slate-900", text: attr.value }),
      ])
    );
  }
  leftColumn.append(contactSection);

  //right column - profile icon
  const rightColumn = el("div", { className: "col-span-1 flex flex-col items-center" });
  rightColumn.append(
    el("img", {
      className: "w-32 h-32 rounded-full border-4 border-slate-300 shadow-lg",
      attrs: { src: "./assets/profile-icon/profile-placeholder.png", alt: "Profile Icon" },
    }),
    el("div", { className: "mt-4 text-sm text-slate-600", text: "Profile Picture" })
  );

  contentWrap.append(leftColumn, rightColumn);
  wrap.append(contentWrap);

  return wrap;
}
