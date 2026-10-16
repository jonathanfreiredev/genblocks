"use client";
import { LogInIcon, LogOutIcon, UserPlusIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Item, ItemContent, ItemMedia, ItemTitle } from "../ui/item";
import Link from "next/link";
import { SheetClose } from "../ui/sheet";
import { logoutAction } from "@/server/auth/auth.actions";

interface SidebarSheetAuthProps {
  isLoggedIn: boolean;
}

export function SidebarSheetAuth({ isLoggedIn }: SidebarSheetAuthProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  return (
    <>
      {!isLoggedIn ? (
        <>
          <SheetClose
            nativeButton={false}
            render={
              <Item
                variant="default"
                size="sm"
                className="cursor-pointer"
                render={
                  <Link href="/auth/login">
                    <ItemMedia>
                      <LogInIcon className="size-5" />
                    </ItemMedia>
                    <ItemContent>
                      <ItemTitle>Log in</ItemTitle>
                    </ItemContent>
                  </Link>
                }
              />
            }
          />
          <SheetClose
            nativeButton={false}
            render={
              <Item
                variant="muted"
                size="sm"
                className="cursor-pointer"
                render={
                  <Link href="/auth/signup">
                    <ItemMedia>
                      <UserPlusIcon className="size-5" />
                    </ItemMedia>
                    <ItemContent>
                      <ItemTitle>Sign up</ItemTitle>
                    </ItemContent>
                  </Link>
                }
              />
            }
          />
        </>
      ) : (
        <SheetClose
          nativeButton={false}
          render={
            <Item
              variant="muted"
              size="sm"
              className="cursor-pointer bg-red-50"
              onClick={async () => {
                if (isSubmitting) return;

                setIsSubmitting(true);
                await logoutAction();
                router.refresh();
                setIsSubmitting(false);
              }}
            >
              <ItemMedia>
                <LogOutIcon className="size-5" />
              </ItemMedia>
              <ItemContent>
                <ItemTitle>Sign out</ItemTitle>
              </ItemContent>
            </Item>
          }
        />
      )}
    </>
  );
}
