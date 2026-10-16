"use client";
import { useState } from "react";
import { Avatar, AvatarFallback } from "./ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import Link from "next/link";
import { Button } from "./ui/button";
import { logoutAction } from "@/server/auth/auth.actions";
import { useRouter } from "next/navigation";

interface DropdownAvatarMenuProps {
  user: {
    name: string;
  };
}
export const DropdownAvatarMenu = ({ user }: DropdownAvatarMenuProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button variant="outline" size="icon-lg" className="rounded-full">
            <Avatar className="cursor-pointer" size="lg">
              <AvatarFallback className="bg-slate-100">
                {user.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </AvatarFallback>
            </Avatar>
          </Button>
        }
      />
      <DropdownMenuContent>
        <DropdownMenuItem render={<Link href="/profile">Profile</Link>} />

        <DropdownMenuSeparator />

        <DropdownMenuItem
          variant="destructive"
          onClick={async () => {
            setIsSubmitting(true);
            await logoutAction();
            router.refresh();
            setIsSubmitting(false);
          }}
          disabled={isSubmitting}
        >
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
