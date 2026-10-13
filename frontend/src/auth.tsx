import { createContext, ReactNode, useContext, useEffect, useState } from "react";

import { api, TOKEN_KEY, User } from "@/src/api";
import { queryClient } from "@/src/query-client";
import { storage } from "@/src/utils/storage";

type AuthCtx = {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, adviserCode?: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const t = await storage.secureGet<string | null>(TOKEN_KEY, null);
      if (t) {
        try {
          setUser(await api<User>("/auth/me"));
        } catch {
          await storage.secureRemove(TOKEN_KEY);
        }
      }
      setLoading(false);
    })();
  }, []);

  const finish = async (r: { token: string; user: User }) => {
    await storage.secureSet(TOKEN_KEY, r.token);
    queryClient.clear();
    setUser(r.user);
  };

  const value: AuthCtx = {
    user,
    loading,
    signIn: async (email, password) =>
      finish(await api("/auth/login", { method: "POST", body: { email: email.trim(), password } })),
    register: async (name, email, password, adviserCode) =>
      finish(
        await api("/auth/register", {
          method: "POST",
          body: { name: name.trim(), email: email.trim(), password, adviser_code: (adviserCode ?? "").trim() },
        }),
      ),
    signOut: async () => {
      await storage.secureRemove(TOKEN_KEY);
      queryClient.clear();
      setUser(null);
    },
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth outside AuthProvider");
  return c;
}
