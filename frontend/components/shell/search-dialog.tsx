"use client";

import { SearchIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "@/components/ui/input-group";
import { catalogueHref, type Section } from "@/lib/vault/links";

const NOUN: Record<Section, string> = {
  blocks: "blocks",
  images: "images",
};

/**
 * Search, as a button that looks like a field until it is one.
 *
 * A permanent input in the chrome would eat the header for a query used once in
 * a while, so the header carries the affordance and the dialog carries the
 * field. The section on screen decides what is searched: the same words mean a
 * title in Blocks and a prompt in Images.
 */
export function SearchDialog({
  section,
  type,
}: {
  section: Section;
  /** The category on screen, when the page is a category rather than an item. */
  type?: string;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setOpen(false);
    router.push(
      catalogueHref({
        section,
        type,
        q: value.trim() || undefined,
        page: 1,
      }),
    );
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) {
          setValue("");
        }
      }}
    >
      <DialogTrigger
        render={
          <Button
            variant="outline"
            className="text-muted-foreground hidden h-8 w-56 justify-start gap-2 rounded-lg px-2.5 font-normal md:inline-flex"
          >
            <SearchIcon className="size-4" />
            <span>search</span>
          </Button>
        }
      />

      <DialogTrigger
        render={
          <Button
            variant="ghost"
            size="icon-sm"
            className="md:hidden"
            aria-label="Search"
          >
            <SearchIcon />
          </Button>
        }
      />

      <DialogContent className="gap-3 sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Search</DialogTitle>
          <DialogDescription>
            Find something in {NOUN[section]}. Press Enter to search.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit}>
          <InputGroup className="h-10">
            <InputGroupAddon>
              <SearchIcon />
            </InputGroupAddon>
            <InputGroupInput
              autoFocus
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder={`Search ${NOUN[section]}`}
              aria-label={`Search ${NOUN[section]}`}
            />
            <InputGroupAddon align="inline-end">
              <InputGroupButton type="submit" size="xs">
                Search
              </InputGroupButton>
            </InputGroupAddon>
          </InputGroup>
        </form>
      </DialogContent>
    </Dialog>
  );
}
