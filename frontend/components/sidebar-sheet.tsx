"use client";
import { MenuIcon, UserIcon, XIcon } from "lucide-react";
import Link from "next/link";
import { SidebarSheetAuth } from "./auth/sidebar-sheet-auth";
import { Button } from "./ui/button";
import { Item, ItemContent, ItemMedia, ItemTitle } from "./ui/item";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "./ui/sheet";

interface SidebarSheetProps {
  isLoggedIn: boolean;
}

export function SidebarSheet({ isLoggedIn }: SidebarSheetProps) {
  return (
    <Sheet>
      <SheetTrigger
        render={
          <Button
            variant="outline"
            size="icon-lg"
            className="rounded-sm"
            aria-label="Open menu"
          >
            <MenuIcon />
          </Button>
        }
      />
      <SheetContent
        side="right"
        className="data-[vaul-Sheet-direction=bottom]:max-h-[50vh] data-[vaul-Sheet-direction=top]:max-h-[50vh]"
      >
        <SheetHeader className="flex flex-row justify-end">
          <SheetTitle className="sr-only">Menu</SheetTitle>
          <SheetClose
            render={
              <Button variant="outline" size="icon-sm" className="rounded-full">
                <XIcon />
              </Button>
            }
          />
        </SheetHeader>
        <div className="flex w-full flex-col gap-0 px-2">
          {isLoggedIn ? (
            <SheetClose
              nativeButton={false}
              render={
                <Item
                  variant="default"
                  size="sm"
                  className="cursor-pointer"
                  render={
                    <Link href="/profile">
                      <ItemMedia>
                        <UserIcon className="size-5" />
                      </ItemMedia>
                      <ItemContent>
                        <ItemTitle>Profile</ItemTitle>
                      </ItemContent>
                    </Link>
                  }
                />
              }
            />
          ) : null}

          <SidebarSheetAuth isLoggedIn={isLoggedIn} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
