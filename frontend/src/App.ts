//import a helper function for creating DOM elements
import { el } from "./shared/lib/dom.js";
//import screen components
import { Dashboard } from "./pages/Dashboard.js";
import { ActiveTickets } from "./pages/ActiveTickets.js";
import { TicketDetail } from "./pages/TicketDetail.js";
import { AccountPage } from "./pages/AccountPage.js";
import { Settings } from "./pages/Settings.js";
import { ClosedTicketsPage } from "./pages/ClosedTickets.js";
import { logout, startLogin } from "./shared/auth.js";
import type { CurrentUserResponse } from "./shared/auth.js";
import type { TicketViewKey } from "./shared/api/aiTickets.js";
//import shared types
import type { BackendTicket } from "./shared/types.js";

type Route =
  | { name: "dashboard" }
  | { name: "active-tickets"; view?: TicketViewKey }
  | { name: "closed-tickets"}
  | { name: "settings" }
  | { name: "account" }
  | { name: "ticket"; ticket: BackendTicket; readOnly?: boolean };

function isTicketViewKey(value: string | undefined): value is TicketViewKey {
  return value === "my-assigned" || value === "my-primary" || value === "my-secondary" || value === "team";
}

//reads the URL hash (after #) and returns the current route as a Route object
function parseHash(): Route {
  const h = location.hash.replace(/^#/, ""); // Remove the #
  if (!h || h === "/") return { name: "dashboard" }; //default route
  const parts = h.split("/").filter(Boolean); // Split by /
  
  //handle different route types
  if (parts[0] === "dashboard") return { name: "dashboard" };
  if (parts[0] === "active-tickets") {
    return { name: "active-tickets", view: isTicketViewKey(parts[1]) ? parts[1] : "my-assigned" };
  }
  if (parts[0] === "team-tickets") return { name: "active-tickets", view: "team" };
  if (parts[0] === "closed-tickets") return { name: "closed-tickets" };
  if (parts[0] === "settings") return { name: "settings" };
  if (parts[0] === "account") return { name: "account" };
  //cannot restore ticket data from URL alone, so redirect to active-tickets
  if (parts[0] === "ticket") return { name: "active-tickets" };
  return { name: "active-tickets" }; //fallback to active tickets 
}

//function to change the URL hash to match the given route
function setHash(route: Route) {
  if (route.name === "dashboard") location.hash = "#/";
  if (route.name === "ticket" && "ticket" in route) {
    location.hash = `#/ticket/${encodeURIComponent(String(route.ticket.autotask_ticket_id))}`;
  }
  if (route.name === "active-tickets") {
    location.hash = route.view && route.view !== "my-assigned"
      ? `#/active-tickets/${route.view}`
      : "#/active-tickets";
  }
  if (route.name === "closed-tickets") location.hash = "#/closed-tickets";
  if (route.name === "settings") location.hash = "#/settings";
  if (route.name === "account") location.hash = "#/account";
}

//Sidebar component: returns a sidebar navigation element
function Sidebar(setRoute: (route: Route) => void): HTMLElement {
  //aside element with tailwind classes 
  const nav = el("aside", { className: "w-64 hidden md:block bg-gradient-to-b from-blue-950 to-cyan-900 border-r border-cyan-800" });
  // Inner container for sidebar content
  const inner = el("div", { className: "p-4" });
  //add title and buttons for all page options
  inner.append(
    el("div", { className: "font-bold text-xl mb-4 text-cyan-200", text: "Ticket Interface" }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-white hover:bg-opacity-20 text-white transition",
      attrs: { type: "button" },
      text: "Dashboard",
    }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-white hover:bg-opacity-20 text-white transition",
      attrs: { type: "button" },
      text: "Active Tickets",
    }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-white hover:bg-opacity-20 text-white transition",
      attrs: { type: "button" },
      text: "Closed Tickets",
    }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-white hover:bg-opacity-20 text-white transition",
      attrs: { type: "button" },
      text: "Settings",
    }),
    el("button", {
      className: "w-full text-left px-3 py-2 rounded hover:bg-white hover:bg-opacity-20 text-white transition",
      attrs: { type: "button" },
      text: "Account",
    }),
  );
  
  //set routes to sidebar buttons for navigation
  const buttons = inner.querySelectorAll("button");
  buttons[0].addEventListener("click", () => setRoute({ name: "dashboard" }));
  buttons[1].addEventListener("click", () => setRoute({ name: "active-tickets", view: "my-assigned" }));
  buttons[2].addEventListener("click", () => setRoute({ name: "closed-tickets" }));
  buttons[3].addEventListener("click", () => setRoute({ name: "settings" }));
  buttons[4].addEventListener("click", () => setRoute({ name: "account" }));
  
  nav.append(inner);
  return nav;
}

//TopHeader component: returns a header bar for the app
function TopHeader(routeName: string, currentUser: CurrentUserResponse): HTMLElement {
  //create a header element
  const hdr = el("header", { className: "bg-gradient-to-r from-blue-950 to-cyan-900 border-b border-cyan-800 m-0" });
  
  //convert route name to display name
  const getDisplayName = (name: string): string => {
    const displayNames: { [key: string]: string } = {
      "dashboard": "DASHBOARD",
      "active-tickets": "ACTIVE TICKETS",
      "closed-tickets": "CLOSED TICKETS",
      "settings": "SETTINGS",
      "account": "ACCOUNT",
      "ticket": "TICKET DETAIL",
    };
    return displayNames[name] || "Tickets";
  };
  
  //add a flex container with centered page title and subtitle on the right
  const name = currentUser.profile.display?.display_name || currentUser.session.display_name;
  const signOutButton = el("button", {
    className: "rounded-lg border border-cyan-200 px-3 py-1 text-sm font-semibold text-cyan-100 transition hover:bg-white hover:text-cyan-900",
    attrs: { type: "button" },
    text: "Sign out",
  });

  signOutButton.addEventListener("click", async () => {
    await logout();
    window.location.reload();
  });

  hdr.append(
    el("div", { className: "px-5 py-3 flex items-center justify-between gap-4" }, [
      el("div", { className: "font-sans font-bold text-xl text-cyan-200", text: "GLOBAL 4" }),
      el("div", { className: "flex-1 flex justify-center" }, [
        el("div", { className: "font-bold text-xl text-cyan-200", text: getDisplayName(routeName) }),
      ]),
      el("div", { className: "flex items-center gap-4" }, [
        el("div", { className: "text-sm font-medium text-cyan-100", text: name }),
        signOutButton,
      ]),
    ])
  );
  return hdr;
}

function SignedOutView(message?: string): HTMLElement {
  const shell = el("div", { className: "min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 via-cyan-50 to-blue-100 p-6" });
  const card = el("div", { className: "w-full max-w-xl rounded-3xl border border-cyan-200 bg-white/90 p-10 shadow-2xl" });
  const button = el("button", {
    className: "mt-8 rounded-xl bg-cyan-700 px-5 py-3 font-semibold text-white transition hover:bg-cyan-800",
    attrs: { type: "button" },
    text: "Sign in with Microsoft",
  });
  button.addEventListener("click", () => startLogin());

  card.append(
    el("div", { className: "text-sm font-semibold uppercase tracking-[0.3em] text-cyan-700", text: "SecOps" }),
    el("h1", { className: "mt-4 text-4xl font-bold text-slate-900", text: "Ticket Interface" }),
    el("p", {
      className: "mt-4 text-base leading-7 text-slate-600",
      text: "Authentication is now handled by Microsoft Entra ID. Sign in to open the dashboard and resolve your profile in the backend service.",
    }),
    ...(message ? [
      el("div", {
        className: "mt-5 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900",
        text: message,
      }),
    ] : []),
    button
  );

  shell.append(card);
  return shell;
}

// Main App function: renders the whole application into the given root element
// root: the HTML element where the app will be mounted
export function App(root: HTMLElement, currentUser: CurrentUserResponse | null, startupMessage?: string) {
  root.innerHTML = ""; //remove any existing content

  if (!currentUser) {
    root.append(SignedOutView(startupMessage));
    return;
  }

  //create the main shell: a flex container for sidebar and main content
  const shell = el("div", { className: "min-h-screen flex gap-0" });
  //main column for header and page content
  const mainCol = el("div", { className: "flex-1 flex flex-col" });

  //main content area element
  const content = el("main", { className: "p-4 md:p-6" });

  //track current route state
  let currentRoute: Route = parseHash();
  let lastSetRoute: Route | null = null;
  let previousRoute: Route = { name: "active-tickets", view: "my-assigned" }; // Track where we came from

  //function to update route and re-render
  const setRoute = (route: Route) => {
    previousRoute = currentRoute; //remember where we came from
    currentRoute = route;
    lastSetRoute = route;
    setHash(route);
    renderRoute();
  };

  //function to render the current route
  const renderRoute = () => {
    const r = currentRoute;
    content.innerHTML = ""; //remove content
    
    //update header to show current page name
    const header = mainCol.querySelector("header");
    if (header) {
      mainCol.removeChild(header);
      mainCol.insertBefore(TopHeader(r.name, currentUser), content);
    }
    
    if (r.name === "dashboard") {
      content.append(Dashboard((ticket) => setRoute({ name: "ticket", ticket })));
    } else if (r.name === "active-tickets") {
      content.append(ActiveTickets(
        (ticket) => setRoute({ name: "ticket", ticket }),
        {
          initialView: r.view ?? "my-assigned",
          onViewChange: (view) => {
            currentRoute = { name: "active-tickets", view };
            lastSetRoute = currentRoute;
            setHash(currentRoute);
          },
        },
      ));
    } else if (r.name === "ticket") {
      content.append(TicketDetail(r.ticket, () => setRoute(previousRoute), { readOnly: r.readOnly }));
    } else if (r.name === "account") {
      content.append(AccountPage(currentUser));
    } else if (r.name === "settings") {
      content.append(Settings(currentUser));
    } else if (r.name === "closed-tickets"){
      content.append(ClosedTicketsPage((ticket) => setRoute({ name: "ticket", ticket, readOnly: true })));
    }
      else {
      //default for other routes like closed-tickets
      content.append(
        el("div", { className: "text-center py-8 text-slate-500", text: `page coming soon` })
      );
    }
    
  };

  //listen for hash changes (URL changes) to update the view
  window.addEventListener("hashchange", () => {
    // If we just set a ticket route and the hash still has that ticket, preserve the ticket data
    if (location.hash.includes("/ticket/") && lastSetRoute?.name === "ticket") {
      currentRoute = lastSetRoute;
      renderRoute();
      return;
    }
    
    currentRoute = parseHash();
    renderRoute();
  });

  //build page layout: header, sidebar, and content
  mainCol.append(TopHeader(currentRoute.name, currentUser), content);
  shell.append(Sidebar(setRoute), mainCol);
  root.append(shell);

  //render the initial route
  renderRoute();
}
