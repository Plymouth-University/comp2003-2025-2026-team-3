import type { BackendTicket } from "../types.js";

function getTimeStamp(): string {
  const now = new Date();
  return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
}

async function fetchTickets(): Promise<BackendTicket[]> {
  const requestStart = performance.now();
  const startTime = getTimeStamp();
  console.log(`[${startTime}] ========== FRONTEND FETCH START ==========`);
  console.log(`[${startTime}] Initiating API request to http://127.0.0.1:8000/api/tickets`);
  
  try {
    const fetchStart = performance.now();
    console.log(`[${getTimeStamp()}] Sending fetch request...`);
    const res = await fetch("http://127.0.0.1:8000/api/tickets");
    const fetchTime = performance.now() - fetchStart;
    console.log(`[${getTimeStamp()}] Network request completed in ${fetchTime.toFixed(1)}ms, status: ${res.status}`);
    
    if (!res.ok) {
      console.error(`[${getTimeStamp()}] API error - Status: ${res.status}`);
      return [];
    }
    
    const textStart = performance.now();
    const text = await res.text();
    const textTime = performance.now() - textStart;
    console.log(`[${getTimeStamp()}] Response text received in ${textTime.toFixed(1)}ms (${text.length} characters)`);
    
    const parseStart = performance.now();
    const json = JSON.parse(text);
    const parseTime = performance.now() - parseStart;
    console.log(`[${getTimeStamp()}] JSON parsed in ${parseTime.toFixed(1)}ms`);
    
    const itemCount = json.items ? json.items.length : 0;
    console.log(`[${getTimeStamp()}] Response contains ${itemCount} items`);
    
    if (!json.items || json.items.length === 0) {
      console.warn(`[${getTimeStamp()}] Warning: No items returned from API`);
      const totalRequestTime = performance.now() - requestStart;
      console.log(`[${getTimeStamp()}] ========== FRONTEND FETCH COMPLETE (EMPTY) ==========`);
      console.log(`[${getTimeStamp()}] Total request time: ${totalRequestTime.toFixed(1)}ms`);
      return [];
    }
    
    if (json.items.length > 0) {
      console.log(`[${getTimeStamp()}] First ticket: ID=${json.items[0].autotask_ticket_id}, Title="${json.items[0].title.substring(0, 50)}..."`);
    }
    
    const totalRequestTime = performance.now() - requestStart;
    console.log(`[${getTimeStamp()}] ========== FRONTEND FETCH COMPLETE ==========`);
    console.log(`[${getTimeStamp()}] Total request time: ${totalRequestTime.toFixed(1)}ms | Network: ${fetchTime.toFixed(1)}ms | Parse: ${parseTime.toFixed(1)}ms`);
    
    return json.items || [];
  } catch (error) {
    const errorTime = performance.now() - requestStart;
    console.error(`[${getTimeStamp()}] FETCH ERROR after ${errorTime.toFixed(1)}ms:`, error);
    console.log(`[${getTimeStamp()}] ========== FRONTEND FETCH FAILED ==========`);
    return [];
  }
}

import { el } from "../lib/dom.js";
import { EllipsisMenu } from "./EllipsisMenu.js";

export function TicketListContainer(onOpenTicket: (ticket: BackendTicket) => void): HTMLElement {
  let ticketsState: BackendTicket[] = [];
  let searchQuery: string = ""; // store search query
  let selectedCompany: string = ""; // store selected company filter
  let selectedQueue: string = ""; // store selected queue filter
  let collapsedCategories: Set<string> = new Set();
  
  //track sort state for each category
  const categorySortState = new Map<string, {
    sortMode: "priority" | "due_date";
    sortByPriority: "asc" | "desc";
    sortByDate: "asc" | "desc";
  }>();

  const mainContainer = el("div", { className: "w-full" });

  //create a search bar element
  const searchBar = el("input", {
    className: "w-full mb-6 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
    attrs: { 
      type: "text", 
      placeholder: "Search tickets by title, ID, or contact..." //search bar hint text
    }
  });
  
  //add input event listener to search bar and update results
  searchBar.addEventListener("input", (e) => {
    searchQuery = (e.target as HTMLInputElement).value.toLowerCase();
    render();
  });

  mainContainer.append(searchBar); //add search bar to the main container

  //create filter buttons container
  const filterContainer = el("div", { className: "mb-6 flex gap-4" });

  //create company filter dropdown
  const companySelect = el("select", {
    className: "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  companySelect.append(el("option", { attrs: { value: "" }, text: "Company Name" }));
  for (let i = 1; i <= 20; i++) {
    companySelect.append(el("option", { attrs: { value: `Company ${i}` }, text: `Company ${i}` }));
  }
  companySelect.addEventListener("change", (e) => {
    selectedCompany = (e.target as HTMLSelectElement).value;
    render();
  });

  //create queue filter dropdown
  const queueSelect = el("select", {
    className: "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  queueSelect.append(el("option", { attrs: { value: "" }, text: "Queue" }));
  queueSelect.append(el("option", { attrs: { value: "MS - Secops" }, text: "MS - Secops" }));
  queueSelect.addEventListener("change", (e) => {
    selectedQueue = (e.target as HTMLSelectElement).value;
    render();
  });

  filterContainer.append(companySelect, queueSelect);
  mainContainer.append(filterContainer);

  const ticketsContainer = el("div", { className: "w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-start" });
  mainContainer.append(ticketsContainer);

  const loadingMsg = el("div", { 
    className: "text-center py-8 text-slate-500 col-span-full",
    text: "Loading tickets..." 
  });
  ticketsContainer.append(loadingMsg);

  //sort tickets within a specific category
  const sortTickets = (tickets: BackendTicket[], category: string): BackendTicket[] => {
    
    //get or initialize sort state for this category
    if (!categorySortState.has(category)) {
      categorySortState.set(category, {
        sortMode: "due_date",
        sortByPriority: "desc",
        sortByDate: "asc"
      });
    }
    
    const state = categorySortState.get(category)!;
    const priorityOrder = { Critical: 4, High: 3, Medium: 2, Low: 1 } as const; //priority hierarchy
    
    const priorityCmp = (a: BackendTicket, b: BackendTicket) => //compare priorities
      (state.sortByPriority === "asc" ? 1 : -1) *
      ((priorityOrder[a.priority as keyof typeof priorityOrder] || 0) - (priorityOrder[b.priority as keyof typeof priorityOrder] || 0));
    
    const dateCmp = (a: BackendTicket, b: BackendTicket) => //compare due dates
      (state.sortByDate === "asc" ? 1 : -1) *
      (new Date(a.due_date).getTime() - new Date(b.due_date).getTime());

    return [...tickets].sort((a, b) => {
      const primary = state.sortMode === "priority" ? priorityCmp(a, b) : dateCmp(a, b);
      if (primary !== 0) return primary;
      return state.sortMode === "priority" ? dateCmp(a, b) : priorityCmp(a, b);
    });
  };

  //make ticket category UI section
  const renderCategorySection = (category: string, tickets: BackendTicket[]) => {
    const isCollapsed = collapsedCategories.has(category);
    
    //initialize sort state for this category if it doesn't exist
    if (!categorySortState.has(category)) {
      categorySortState.set(category, {
        sortMode: "due_date",
        sortByPriority: "desc",
        sortByDate: "asc"
      });
    }
    
    const section = el("div", {
      className: "bg-white rounded-lg shadow border border-blue-100 max-h-96 overflow-y-auto",
    });

    const header = el("div", { className: "flex items-center justify-between p-4 border-b border-slate-100 hover:bg-blue-50" });
    
    const titleWrap = el("div", { className: "flex items-center gap-2 flex-1" });
    titleWrap.append(
      el("span", { className: "font-bold text-lg capitalize text-slate-900", text: category }),
      el("span", { className: "text-sm text-slate-500", text: `(${tickets.length})` })
    );

    //create button row for sort buttons
    const btnRow = el("div", { className: "flex gap-2" });

    //create sort by date button
    const dateBtn = el("button", { 
      className: "p-1 hover:bg-slate-200 rounded transition",
      attrs: { type: "button" } 
    });
    dateBtn.append(
      el("img", {
        className: "w-5 h-5",
        attrs: { src: "./assets/sort-by-icon/sortIcon.png", alt: "Sort by Date" },
      })
    );

    //create sort by priority button
    const priorityBtn = el("button", { 
      className: "p-1 hover:bg-slate-200 rounded transition",
      attrs: { type: "button" } 
    });
    priorityBtn.append(
      el("img", {
        className: "w-5 h-5",
        attrs: { src: "./assets/priority-icon/danger.png", alt: "Sort by Priority" },
      })
    );

    btnRow.append(dateBtn, priorityBtn);

    const icon = el("span", { 
      className: `text-slate-400 text-lg transition-transform ${isCollapsed ? "" : "rotate-180"}`,
      text: "▼"
    });

    header.append(titleWrap, btnRow, icon); //add title, icon and buttons to category container header

    //tickets container element
    const ticketsWrap = el("div", { className: "divide-y divide-slate-100" });

    if (!isCollapsed) {
      //sort tickets for this category
      const sortedTickets = sortTickets(tickets, category);
      
      for (const ticket of sortedTickets) {
        const ticketCard = el("div", {
          className: "p-4 hover:bg-emerald-200 cursor-pointer transition relative",
          attrs: { role: "button" }
        });

        //create an ellipsis menu for each ticket
        const menu = EllipsisMenu();
        menu.addEventListener("view", () => onOpenTicket(ticket)); // on view, open ticket

        //ticket title row
        const topRow = el("div", { className: "flex justify-between items-start gap-3 mb-3" }, [
          el("div", { className: "font-semibold text-slate-900 truncate flex-1", text: ticket.title }), //add title
          menu
        ]);

        //ticket info row
        const infoRow = el("div", { className: "flex justify-between items-start gap-3" }, [
          el("div", { className: "min-w-0 flex-1" }, [
            el("div", { className: "text-xs text-slate-500", text: `ID: ${ticket.autotask_ticket_id}` }), //show id
            el("div", { className: "text-xs text-slate-500 mt-2 flex gap-2" }, [
              el("span", { text: `Priority: ${ticket.priority}` }), //show priority
              el("span", { text: `Confidence: ${(ticket.ai.confidence * 100).toFixed(0)}%` }) //show ai confidence
            ]),
            el("div", { className: "text-xs text-slate-500 mt-2", text: `Due: ${ticket.due_date}` }) // show the due date
          ])
        ]);

        ticketCard.append(topRow, infoRow);

        ticketCard.addEventListener("click", (e) => {
          //dont complete navigation if clicking on menu
          if ((e.target as HTMLElement).closest('.relative')) {
            return;
          }
          onOpenTicket(ticket);
        });

        ticketsWrap.append(ticketCard);
      }
    }

    //filter button event listeners - using stored category reference
    const sortCategory = category;
    
    dateBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const state = categorySortState.get(sortCategory)!;
      state.sortMode = "due_date";
      state.sortByDate = state.sortByDate === "asc" ? "desc" : "asc";
      render();
    });

    priorityBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const state = categorySortState.get(sortCategory)!;
      state.sortMode = "priority";
      state.sortByPriority = state.sortByPriority === "asc" ? "desc" : "asc";
      render();
    });

    //toggle collapse of category container
    header.addEventListener("click", (e) => {
      //don't collapse if clicking on buttons
      if ((e.target as HTMLElement).closest('button')) {
        e.stopPropagation();
        return;
      }
      if (collapsedCategories.has(sortCategory)) {
        collapsedCategories.delete(sortCategory);
      } else {
        collapsedCategories.add(sortCategory);
      }
      render();
    });

    section.append(header, ticketsWrap);
    return section;
  };

  const render = () => {
    const renderStart = performance.now();
    const startTime = getTimeStamp();
    console.log(`[${startTime}] ========== FRONTEND RENDER START ==========`);
    console.log(`[${startTime}] Input: ${ticketsState.length} total tickets, filters: search="${searchQuery}" company="${selectedCompany}" queue="${selectedQueue}"`);
    
    ticketsContainer.innerHTML = "";
    
    //filter tickets based on search query and selected filters
    let filteredTickets = ticketsState;
    const filterStart = performance.now();
    if (searchQuery) {
      filteredTickets = filteredTickets.filter(ticket => {
        const searchableText = `${ticket.title} ${ticket.autotask_ticket_id} ${ticket.company} ${ticket.contact}`.toLowerCase();
        return searchableText.includes(searchQuery);
      });
      console.log(`[${getTimeStamp()}] Search filter applied: ${filteredTickets.length} tickets match`);
    }
    
    if (selectedCompany) {
      filteredTickets = filteredTickets.filter(ticket => ticket.company === selectedCompany);
      console.log(`[${getTimeStamp()}] Company filter applied: ${filteredTickets.length} tickets match`);
    }
    
    if (selectedQueue) {
      filteredTickets = filteredTickets.filter(ticket => ticket.queue === selectedQueue);
      console.log(`[${getTimeStamp()}] Queue filter applied: ${filteredTickets.length} tickets match`);
    }
    
    const filterTime = performance.now() - filterStart;
    console.log(`[${getTimeStamp()}] Filtering complete in ${filterTime.toFixed(1)}ms - ${filteredTickets.length} tickets to display`);
    
    if (filteredTickets.length === 0) { //if there are no tickets, display message
      ticketsContainer.append(
        el("div", { 
          className: "text-center py-8 text-slate-500 col-span-full", 
          text: searchQuery || selectedCompany || selectedQueue ? "No tickets found matching your filters" : "No tickets found" 
        })
      );
      const totalRenderTime = performance.now() - renderStart;
      console.log(`[${getTimeStamp()}] ========== FRONTEND RENDER COMPLETE (EMPTY) ==========`);
      console.log(`[${getTimeStamp()}] Total render time: ${totalRenderTime.toFixed(1)}ms`);
      return;
    }

    //group tickets by the category
    const categorizeStart = performance.now();
    const categorized = new Map<string, BackendTicket[]>();
    for (const ticket of filteredTickets) {
      const cat = ticket.ai?.category || "uncategorized";
      if (!categorized.has(cat)) {
        categorized.set(cat, []);
      }
      categorized.get(cat)!.push(ticket);
    }
    const categorizeTime = performance.now() - categorizeStart;
    console.log(`[${getTimeStamp()}] Categorization complete in ${categorizeTime.toFixed(1)}ms - ${categorized.size} categories found`);

    //sort the categories and render UI sections
    const renderUIStart = performance.now();
    const sortedCategories = Array.from(categorized.keys()).sort();
    console.log(`[${getTimeStamp()}] Rendering UI for ${sortedCategories.length} categories...`);
    for (const category of sortedCategories) {
      const tickets = categorized.get(category) || [];
      ticketsContainer.append(renderCategorySection(category, tickets));
    }
    const renderUITime = performance.now() - renderUIStart;
    console.log(`[${getTimeStamp()}] UI rendering complete in ${renderUITime.toFixed(1)}ms`);
    
    const totalRenderTime = performance.now() - renderStart;
    console.log(`[${getTimeStamp()}] ========== FRONTEND RENDER COMPLETE ==========`);
    console.log(`[${getTimeStamp()}] TIMING BREAKDOWN: Filter=${filterTime.toFixed(1)}ms | Categorize=${categorizeTime.toFixed(1)}ms | RenderUI=${renderUITime.toFixed(1)}ms | Total=${totalRenderTime.toFixed(1)}ms`);
  };

  //fetch tickets and render UI
  const loadStart = performance.now();
  const loadStartTime = getTimeStamp();
  console.log(`[${loadStartTime}] ========== TICKET LOAD INITIATED ==========`);
  console.log(`[${loadStartTime}] Calling fetchTickets()...`);
  fetchTickets().then(t => {
    const fetchCompleteTime = getTimeStamp();
    const fetchElapsed = performance.now() - loadStart;
    console.log(`[${fetchCompleteTime}] fetchTickets() completed in ${fetchElapsed.toFixed(1)}ms, received ${t.length} tickets`);
    console.log(`[${fetchCompleteTime}] Updating state and calling render()...`);
    ticketsState = t;
    render();
    const totalLoadTime = performance.now() - loadStart;
    console.log(`[${getTimeStamp()}] ========== COMPLETE TICKET LOAD SEQUENCE FINISHED ==========`);
    console.log(`[${getTimeStamp()}] Total time from initiation to full render: ${totalLoadTime.toFixed(1)}ms`);
  });

  return mainContainer;
}
