//import a helper function for creating DOM elements
import { el } from "./lib/dom.js";
//import screen components
import { Dashboard } from "./screens/Dashboard.js";
import { ActiveTickets } from "./screens/ActiveTickets.js";
import { TicketDetail } from "./screens/TicketDetail.js";

type BackendTicket = {
  autotask_ticket_id: number;
  ticket_number: string;
  company: string;
  contact: string;
  status: string;
  priority: string;
  created: string;
  title: string;
  description: string;
  due_date: string;
  ai: {
    category: string;
    confidence: number;
  };
};

//define a TypeScript type for the possible routes in the app
//"dashboard" is the main page, "active-tickets" is the page for all active tickets etc. 
type Route =
  | { name: "dashboard" }
  | { name: "active-tickets"}
  | { name: "closed-tickets"}
  | { name: "settings" }
  | { name: "account" }
  | { name: "ticket"; ticket: BackendTicket };

//reads the URL hash (after #) and returns the current route as a Route object
function parseHash(): Route {
  const h = location.hash.replace(/^#/, ""); // Remove the #
  if (!h || h === "/") return { name: "dashboard" }; //default route
  const parts = h.split("/").filter(Boolean); // Split by /
  //cannot restore ticket data from URL alone, so redirect to active-tickets
  if (parts[0] === "ticket") return { name: "active-tickets" };
  return { name: "active-tickets" }; //fallback to active tickets 
}

//function to change the URL hash to match the given route
function setHash(route: Route) {
  if (route.name === "dashboard") location.hash = "#/";
  if (route.name === "ticket") location.hash = `#/ticket/${encodeURIComponent(String(route.ticket.autotask_ticket_id))}`;
  if (route.name === "active-tickets") location.hash = "#/active-tickets";
  if (route.name === "closed-tickets") location.hash = "#/closed-tickets";
  if (route.name === "settings") location.hash = "#/settings";
  if (route.name === "account") location.hash = "#/account";
}

//Sidebar component: returns a sidebar navigation element
function Sidebar(setRoute: (route: Route) => void): HTMLElement {
  //aside element with tailwind classes 
  const nav = el("aside", { className: "w-64 hidden md:block bg-gradient-to-t from-[#104069] to-[#1a6a9f] border-r border-slate-200" });
  // Inner container for sidebar content
  const inner = el("div", { className: "p-4" });
  //add title and buttons for all page options
  inner.append(
    el("div", { className: "font-bold text-lg mb-4 text-white", text: "Global 4 - Ticket Interface" }),
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
  buttons[1].addEventListener("click", () => setRoute({ name: "active-tickets" }));
  buttons[2].addEventListener("click", () => setRoute({ name: "closed-tickets" }));
  buttons[3].addEventListener("click", () => setRoute({ name: "settings" }));
  buttons[4].addEventListener("click", () => setRoute({ name: "account" }));
  
  nav.append(inner);
  return nav;
}

//TopHeader component: returns a header bar for the app
function TopHeader(): HTMLElement {
  //create a header element
  const hdr = el("header", { className: "bg-gradient-to-r from-[#104069] to-[#1a6a9f] border-b border-slate-300 m-0" });
  //add a flex container with a title and a subtitle
  hdr.append(
    el("div", { className: "px-5 py-3 flex items-center justify-between" }, [
      el("div", { className: "font-semibold text-lg text-white", text: "Tickets" }),
      el("div", { className: "font-mono font-semibold text-lg text-white", text: "GLOBAL 4" }),
    ])
  );
  return hdr;
}

// Main App function: renders the whole application into the given root element
// root: the HTML element where the app will be mounted
export function App(root: HTMLElement) {
  root.innerHTML = ""; // Clear any existing content

  //create the main shell: a flex container for sidebar and main content
  const shell = el("div", { className: "min-h-screen flex" });
  //main column for header and page content
  const mainCol = el("div", { className: "flex-1 flex flex-col" });

  //main content area element
  const content = el("main", { className: "p-4 md:p-6" });

  //track current route state
  let currentRoute: Route = parseHash();

  //function to update route and re-render
  const setRoute = (route: Route) => {
    currentRoute = route;
    setHash(route);
    renderRoute();
  };

  //function to render the current route
  const renderRoute = () => {
    const r = currentRoute;
    content.innerHTML = ""; //remove content
    
    if (r.name === "dashboard") {
      content.append(Dashboard());
    } else if (r.name === "active-tickets") {
      content.append(ActiveTickets((ticket) => setRoute({ name: "ticket", ticket })));
    } else if (r.name === "ticket") {
      content.append(TicketDetail(r.ticket, () => setRoute({ name: "active-tickets" })));
    } else {
      //default for other routes like closed-tickets, settings, account
      content.append(
        el("div", { className: "text-center py-8 text-slate-500", text: `${r.name} page coming soon` })
      );
    }
  };

  //listen for hash changes (URL changes) to update the view
  window.addEventListener("hashchange", () => {
    currentRoute = parseHash();
    renderRoute();
  });

  //build page layout: header, sidebar, and content
  mainCol.append(TopHeader(), content);
  shell.append(Sidebar(setRoute), mainCol);
  root.append(shell);

  //render the initial route
  renderRoute();
}
