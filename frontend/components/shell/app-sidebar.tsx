"use client";

import {
  FlagIcon,
  ImageIcon,
  LayoutGrid,
  ListChecks,
  PanelLeftClose,
  PanelLeftOpen,
  Users,
  XIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Brand } from "@/components/shell/brand";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { AgentChatTrigger } from "@/components/vault/agent-chat";
import { cn } from "@/lib/utils";
import {
  SECTION_KIND,
  sectionFromPath,
  typeFromPath,
  type Section,
} from "@/lib/vault/links";
import type { Category } from "@/lib/vault/types";

const SECTIONS: { section: Section; label: string; icon: typeof LayoutGrid }[] =
  [
    { section: "blocks", label: "Blocks", icon: LayoutGrid },
    { section: "images", label: "Images", icon: ImageIcon },
  ];

/**
 * The navigation, as shadcn's sidebar.
 *
 * On a laptop it is the full-height column: the mark, the one action, the two
 * sections and the taxonomy of whichever section is open. On a phone the same
 * component becomes a sheet that starts under the header, so the header keeps
 * the way back and the sheet keeps the list.
 */
export function AppSidebar({
  categories,
  isAdmin,
}: {
  categories: Category[];
  isAdmin: boolean;
}) {
  const pathname = usePathname();
  const { isMobile, open, setOpenMobile, toggleSidebar } = useSidebar();

  const inSection =
    pathname === "/blocks" ||
    pathname.startsWith("/blocks/") ||
    pathname === "/images" ||
    pathname.startsWith("/images/");

  // Outside the vault (tasks, profile) the categories still belong to Blocks:
  // there is no third kind and an empty column would read as a bug.
  const section: Section = inSection ? sectionFromPath(pathname) : "blocks";
  const kind = SECTION_KIND[section];
  const types = categories.filter(
    (category) => category.kind === kind && category.level === 2,
  );
  // Only a taxonomy slug selects a category; an item slug is just an item.
  const activeType = inSection
    ? typeFromPath(
        pathname,
        section,
        types.map((type) => type.slug),
      )
    : undefined;

  function closeOnMobile() {
    if (isMobile) {
      setOpenMobile(false);
    }
  }

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-[var(--header-height)] justify-center border-b p-2 group-data-[collapsible=icon]:h-auto group-data-[collapsible=icon]:py-2">
        <div className="hidden items-center gap-1 group-data-[collapsible=icon]:flex-col md:flex">
          <Brand className="min-w-0 flex-1 group-data-[collapsible=icon]:hidden" />
          <Brand
            compact
            className="hidden group-data-[collapsible=icon]:flex"
          />
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={toggleSidebar}
            aria-label={open ? "Collapse the sidebar" : "Expand the sidebar"}
            aria-expanded={open}
          >
            {open ? <PanelLeftClose /> : <PanelLeftOpen />}
          </Button>
        </div>

        <div className="flex items-center justify-between md:hidden">
          <span className="text-muted-foreground px-2 text-xs font-medium tracking-wide uppercase">
            Menu
          </span>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={() => setOpenMobile(false)}
            aria-label="Close the navigation"
          >
            <XIcon />
          </Button>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {/* On a phone the assistant floats at the bottom of the page instead. */}
        <SidebarGroup className="hidden md:block">
          <SidebarGroupContent>
            <AgentChatTrigger className="h-9 w-full group-data-[collapsible=icon]:px-0" />
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Browse</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {SECTIONS.map(({ section: one, label, icon: Icon }) => {
                const active = inSection && section === one;

                return (
                  <SidebarMenuItem key={one}>
                    <SidebarMenuButton
                      render={<Link href={`/${one}`} onClick={closeOnMobile} />}
                      isActive={active}
                      tooltip={label}
                    >
                      <Icon />
                      <span>{label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {isAdmin ? (
          <SidebarGroup>
            <SidebarGroupLabel>Operate</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    render={
                      <Link href="/admin/items" onClick={closeOnMobile} />
                    }
                    isActive={pathname.startsWith("/admin/items")}
                    tooltip="Items"
                  >
                    <ListChecks />
                    <span>Items</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    render={
                      <Link href="/admin/reports" onClick={closeOnMobile} />
                    }
                    isActive={pathname.startsWith("/admin/reports")}
                    tooltip="Reports"
                  >
                    <FlagIcon />
                    <span>Reports</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    render={
                      <Link href="/admin/users" onClick={closeOnMobile} />
                    }
                    isActive={pathname.startsWith("/admin/users")}
                    tooltip="Users"
                  >
                    <Users />
                    <span>Users</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ) : null}

        <SidebarGroup className="group-data-[collapsible=icon]:hidden">
          <SidebarGroupLabel>Categories</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  render={<Link href={`/${section}`} onClick={closeOnMobile} />}
                  isActive={inSection && !activeType}
                  size="sm"
                  className="pl-7"
                >
                  <span className="text-muted-foreground text-xs">All</span>
                </SidebarMenuButton>
              </SidebarMenuItem>

              {types.map((type) => {
                const active = activeType === type.slug;

                return (
                  <SidebarMenuItem key={type.id}>
                    <SidebarMenuButton
                      render={
                        <Link
                          href={`/${section}/${type.slug}`}
                          onClick={closeOnMobile}
                        />
                      }
                      isActive={active}
                      size="sm"
                      className="pl-7"
                    >
                      <span
                        aria-hidden
                        className={cn(
                          "size-1.5 shrink-0 rounded-full bg-current",
                          active ? "opacity-100" : "opacity-30",
                        )}
                      />
                      <span>{type.name}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-2">
        <div className="flex items-center justify-between gap-2 group-data-[collapsible=icon]:flex-col">
          <ThemeToggle />
          <a
            href="https://github.com/jonathanfreiredev/genblocks"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground text-xs transition-colors group-data-[collapsible=icon]:hidden"
          >
            Source
          </a>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
