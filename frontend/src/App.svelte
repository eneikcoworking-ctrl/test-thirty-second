<script>
  import { onMount } from 'svelte';

  // Core data logic and persistent state management
  let notes = [
    {
      id: 1,
      title: 'Mobile App Design System',
      body: 'Finalizing the visual tokens for the new design language. We need to ensure that the primary action buttons have sufficient contrast ratios for accessibility.',
      createdAt: '2026-10-24T10:00:00.000Z',
      updatedAt: '2026-10-24T10:00:00.000Z',
      tags: ['Design', 'Priority']
    },
    {
      id: 2,
      title: 'Quarterly Design Review',
      body: 'The stakeholder feedback on the landing page design was generally positive. Key takeaway: shorten the onboarding flow to 3 steps.',
      createdAt: '2026-10-12T14:30:00.000Z',
      updatedAt: '2026-10-12T14:30:00.000Z',
      tags: ['Design', 'Archive']
    },
    {
      id: 3,
      title: 'Project Echo: Design Sprint',
      body: 'Collaborative session with the product team to define the core user journeys. Focus on the \'Focus Mode\' design and notification hierarchy.',
      createdAt: '2026-09-28T09:15:00.000Z',
      updatedAt: '2026-09-28T09:15:00.000Z',
      tags: ['Design', 'Echo']
    }
  ];

  // Load from localStorage if present
  onMount(() => {
    const saved = localStorage.getItem('project_notes');
    if (saved) {
      try {
        notes = JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse notes from storage', e);
      }
    }
  });

  function saveNotes() {
    localStorage.setItem('project_notes', JSON.stringify(notes));
  }

  // Filter & Search states
  let searchQuery = '';
  let selectedTag = 'All';

  // Available unique tags across all notes
  $: allTags = ['All', ...new Set(notes.flatMap(n => n.tags || []))];

  // Create & Edit form state
  let showForm = false;
  let editingNoteId = null;
  let formTitle = '';
  let formBody = '';
  let formTagsInput = '';

  // Filter notes newest-first (sort by createdAt)
  $: filteredNotes = notes
    .filter(note => {
      // real-time search/filter by title
      const matchesSearch = note.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesTag = selectedTag === 'All' || (note.tags && note.tags.includes(selectedTag));
      return matchesSearch && matchesTag;
    })
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  // Form handling functions
  function handleOpenCreate() {
    editingNoteId = null;
    formTitle = '';
    formBody = '';
    formTagsInput = '';
    showForm = true;
  }

  function handleOpenEdit(note) {
    editingNoteId = note.id;
    formTitle = note.title;
    formBody = note.body;
    formTagsInput = (note.tags || []).join(', ');
    showForm = true;
  }

  function handleSaveNote() {
    if (!formTitle.trim()) {
      alert('Title is required');
      return;
    }

    const tags = formTagsInput
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0);

    const now = new Date().toISOString();

    if (editingNoteId) {
      // Update
      notes = notes.map(n => {
        if (n.id === editingNoteId) {
          return {
            ...n,
            title: formTitle.trim(),
            body: formBody.trim(),
            tags,
            updatedAt: now
          };
        }
        return n;
      });
    } else {
      // Create
      const newId = notes.length > 0 ? Math.max(...notes.map(n => n.id)) + 1 : 1;
      const newNote = {
        id: newId,
        title: formTitle.trim(),
        body: formBody.trim(),
        createdAt: now,
        updatedAt: now,
        tags
      };
      notes = [...notes, newNote];
    }

    saveNotes();
    showForm = false;
    editingNoteId = null;
    formTitle = '';
    formBody = '';
    formTagsInput = '';
  }

  function handleDeleteNote(id) {
    if (confirm('Are you sure you want to delete this note?')) {
      notes = notes.filter(n => n.id !== id);
      saveNotes();
      if (editingNoteId === id) {
        showForm = false;
        editingNoteId = null;
      }
    }
  }

  function handleClearSearch() {
    searchQuery = '';
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[d.getMonth()]} ${d.getDate()}`;
  }

  // HTML escape to prevent XSS
  function escapeHTML(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Highlight matches in text safely
  function getHighlightedHTML(text, query) {
    const escapedText = escapeHTML(text);
    if (!query) return escapedText;
    const escapedQuery = escapeHTML(query);
    const regex = new RegExp(`(${escapeRegExp(escapedQuery)})`, 'gi');
    return escapedText.replace(regex, '<span class="search-highlight">$1</span>');
  }

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
</script>

<div class="min-h-screen bg-background text-on-background font-sans pb-24">
  <!-- TopAppBar -->
  <header class="fixed top-0 left-0 w-full z-50 bg-surface border-b border-outline-variant flex justify-between items-center px-container-margin h-14">
    <div class="flex items-center gap-4">
      <button
        class="material-symbols-outlined text-primary hover:bg-surface-container transition-colors p-2 rounded-full cursor-pointer"
        aria-label="Menu"
      >
        menu
      </button>
      <h1 class="text-headline-md font-bold text-primary tracking-tight">FocusNotes</h1>
    </div>
    <div class="flex items-center gap-4">
      <button
        on:click={handleOpenCreate}
        class="px-4 py-1.5 rounded-full text-label-md bg-primary text-on-primary font-semibold hover:opacity-90 transition-opacity flex items-center gap-1 cursor-pointer"
        aria-label="Add new note"
      >
        <span class="material-symbols-outlined text-base">add</span>
        New Note
      </button>
      <div class="w-8 h-8 rounded-full overflow-hidden border border-outline-variant">
        <img class="w-full h-full object-cover" alt="User Profile" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBx3zlSk6411IN8cJdOM680aMx5BwJOnLJC7E2kcNrbju5CaDgQQeux9G69aJM5v5ruHkvprNNVH8opSqYt4trNXUjOIXFRzpvLSswGW070vrhULNSjLQIflX3qEHQufHt2Jb1Y8bD90goI-uHGLW3fcaoDhBljS68Ud4Eqs68on0X_r7RGFPO-233wOfLiQmzQHpq5fvmfFsF3NsPc6NYAyf0xVXo0yz00Ny-gzVyXmsX1rvESRkqD_uPpbAAWd2i1nYlObqCR-pU"/>
      </div>
    </div>
  </header>

  <!-- Main Content Canvas -->
  <main class="mt-14 px-container-margin pt-6 max-w-3xl mx-auto">

    {#if showForm}
      <!-- Modal Form Container -->
      <section
        class="mb-8 p-6 bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm"
        aria-labelledby="form-heading"
      >
        <h2 id="form-heading" class="text-headline-lg font-bold text-on-background mb-4">
          {editingNoteId ? 'Edit Note' : 'Create Note'}
        </h2>
        <div class="space-y-4">
          <div>
            <label for="note-title" class="block text-label-md font-semibold text-on-surface-variant mb-1">Title</label>
            <input
              id="note-title"
              type="text"
              bind:value={formTitle}
              class="w-full px-4 py-2 border border-outline rounded-xl focus:ring-2 focus:ring-primary focus:outline-none bg-surface-container-low text-body-md"
              placeholder="Note title..."
            />
          </div>
          <div>
            <label for="note-body" class="block text-label-md font-semibold text-on-surface-variant mb-1">Body Text</label>
            <textarea
              id="note-body"
              bind:value={formBody}
              rows="4"
              class="w-full px-4 py-2 border border-outline rounded-xl focus:ring-2 focus:ring-primary focus:outline-none bg-surface-container-low text-body-md"
              placeholder="Note body text..."
            ></textarea>
          </div>
          <div>
            <label for="note-tags" class="block text-label-md font-semibold text-on-surface-variant mb-1">Tags (comma separated)</label>
            <input
              id="note-tags"
              type="text"
              bind:value={formTagsInput}
              class="w-full px-4 py-2 border border-outline rounded-xl focus:ring-2 focus:ring-primary focus:outline-none bg-surface-container-low text-body-md"
              placeholder="e.g. Design, Priority, Feedback"
            />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button
              on:click={() => showForm = false}
              class="px-4 py-2 rounded-xl text-label-md font-semibold text-on-surface-variant hover:bg-surface-container transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              on:click={handleSaveNote}
              class="px-5 py-2 rounded-xl text-label-md font-semibold bg-primary text-on-primary hover:opacity-90 transition-opacity cursor-pointer"
            >
              Save Note
            </button>
          </div>
        </div>
      </section>
    {/if}

    <!-- Search Header -->
    <div class="sticky top-14 bg-background/95 backdrop-blur-sm pt-2 pb-4 z-40">
      <div class="relative flex items-center mb-6">
        <span class="material-symbols-outlined absolute left-4 text-on-surface-variant" aria-hidden="true">search</span>
        <input
          class="w-full h-12 pl-12 pr-12 bg-surface-container-low border-none rounded-xl focus:ring-2 focus:ring-primary transition-all text-body-md placeholder:text-on-surface-variant/50"
          placeholder="Search your notes by title..."
          type="text"
          bind:value={searchQuery}
          aria-label="Search notes"
        />
        {#if searchQuery}
          <button
            on:click={handleClearSearch}
            class="absolute right-4 text-primary font-label-md hover:bg-surface-container transition-colors px-2 py-1 rounded cursor-pointer"
            aria-label="Clear search input"
          >
            Clear
          </button>
        {/if}
      </div>

      <!-- Filter Chips -->
      <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" role="group" aria-label="Filter notes by tag">
        {#each allTags as tag}
          <button
            on:click={() => selectedTag = tag}
            class="flex-shrink-0 px-4 py-2 rounded-full text-label-sm transition-all border border-outline-variant cursor-pointer
              {selectedTag === tag ? 'bg-primary text-on-primary shadow-sm' : 'bg-surface-container-high text-on-surface-variant hover:bg-outline-variant'}"
          >
            {tag}
          </button>
        {/each}
      </div>
    </div>

    <!-- Search Results Count -->
    <div class="mb-4" aria-live="polite">
      <p class="text-label-sm text-on-surface-variant uppercase tracking-wider">
        {filteredNotes.length} Results found {searchQuery ? `for "${searchQuery}"` : ''}
      </p>
    </div>

    <!-- Search Results List -->
    <div class="space-y-4">
      {#each filteredNotes as note (note.id)}
        <div
          class="p-5 bg-surface-container-lowest border border-outline-variant rounded-xl hover:bg-surface-container-low transition-all cursor-pointer group relative"
          role="article"
          aria-labelledby="note-title-{note.id}"
        >
          <div class="flex justify-between items-start mb-2 pr-16">
            <h3 id="note-title-{note.id}" class="font-headline-md text-headline-md text-on-background group-hover:text-primary transition-colors">
              {@html getHighlightedHTML(note.title, searchQuery)}
            </h3>
            <span class="text-label-sm text-on-surface-variant whitespace-nowrap">{formatDate(note.createdAt)}</span>
          </div>

          <p class="text-body-md text-on-surface-variant line-clamp-2 leading-relaxed mb-4">
            {note.body}
          </p>

          <div class="flex justify-between items-center">
            <div class="flex gap-2">
              {#if note.tags}
                {#each note.tags as tag}
                  <span class="px-2 py-1 rounded bg-surface-container text-[0.625rem] font-bold text-on-surface-variant uppercase">
                    {tag}
                  </span>
                {/each}
              {/if}
            </div>

            <div class="flex gap-2 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity absolute right-5 bottom-5">
              <button
                on:click|stopPropagation={() => handleOpenEdit(note)}
                class="p-1.5 text-primary hover:bg-surface-container rounded-full cursor-pointer"
                aria-label="Edit note"
              >
                <span class="material-symbols-outlined text-lg">edit</span>
              </button>
              <button
                on:click|stopPropagation={() => handleDeleteNote(note.id)}
                class="p-1.5 text-error hover:bg-error-container rounded-full cursor-pointer"
                aria-label="Delete note"
              >
                <span class="material-symbols-outlined text-lg">delete</span>
              </button>
            </div>
          </div>
        </div>
      {:else}
        <!-- Empty State Hint -->
        <div class="flex flex-col items-center justify-center py-20 text-center">
          <span class="material-symbols-outlined text-6xl text-outline-variant mb-4" aria-hidden="true">search_off</span>
          <h4 class="font-headline-md text-on-surface">No notes found</h4>
          <p class="text-body-md text-on-surface-variant">Try a different keyword or filter.</p>
        </div>
      {/each}
    </div>
  </main>

  <!-- BottomNavBar -->
  <nav class="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center py-2 bg-surface border-t border-outline-variant h-16">
    <button class="flex flex-col items-center justify-center text-on-surface-variant hover:bg-surface-container-low transition-all p-2 rounded-lg cursor-pointer">
      <span class="material-symbols-outlined">dashboard</span>
      <span class="font-label-sm text-label-sm">Dashboard</span>
    </button>
    <!-- ACTIVE TAB: Search -->
    <button class="flex flex-col items-center justify-center text-primary font-semibold hover:bg-surface-container-low transition-all scale-95 duration-100 p-2 rounded-lg cursor-pointer">
      <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">search</span>
      <span class="font-label-sm text-label-sm">Search</span>
    </button>
    <button class="flex flex-col items-center justify-center text-on-surface-variant hover:bg-surface-container-low transition-all p-2 rounded-lg cursor-pointer">
      <span class="material-symbols-outlined">folder_open</span>
      <span class="font-label-sm text-label-sm">Projects</span>
    </button>
    <button class="flex flex-col items-center justify-center text-on-surface-variant hover:bg-surface-container-low transition-all p-2 rounded-lg cursor-pointer">
      <span class="material-symbols-outlined">settings</span>
      <span class="font-label-sm text-label-sm">Settings</span>
    </button>
  </nav>
</div>
