<script lang="ts">
  import * as Sidebar from '$lib/components/ui/sidebar/index.js';
  import { pages, type Page } from './navigation';

  let { page, onNavigate }: { page: Page; onNavigate: (page: Page) => void } = $props();
  const sidebar = Sidebar.useSidebar();

  function navigate(destination: Page) {
    onNavigate(destination);
    if (sidebar.isMobile) sidebar.setOpenMobile(false);
  }
</script>

<Sidebar.Group>
  <Sidebar.GroupLabel>Workspace</Sidebar.GroupLabel>
  <Sidebar.GroupContent>
    <Sidebar.Menu>
      {#each pages as item (item.id)}
        <Sidebar.MenuItem>
          <Sidebar.MenuButton isActive={page === item.id} aria-current={page === item.id ? 'page' : undefined} aria-label={item.label} tooltipContent={item.label} onclick={() => navigate(item.id)}>
            <item.icon aria-hidden="true" />
            <span>{item.label}</span>
          </Sidebar.MenuButton>
        </Sidebar.MenuItem>
      {/each}
    </Sidebar.Menu>
  </Sidebar.GroupContent>
</Sidebar.Group>
