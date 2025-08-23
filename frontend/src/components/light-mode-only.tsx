"use client";

import { ReactNode, useEffect } from "react";

interface LightModeOnlyProps {
  children: ReactNode;
}

export function LightModeOnly({ children }: LightModeOnlyProps) {
  useEffect(() => {
    // Force light mode by adding the light class and removing dark
    const root = document.documentElement;
    root.classList.add("light");
    root.classList.remove("dark");
    
    // Cleanup function to restore original theme when component unmounts
    return () => {
      // Only restore if we're not on a light-mode-only page
      const currentPath = window.location.pathname;
      const lightModeOnlyPages = ['/', '/login', '/register', '/forgot-password', '/reset-password'];
      
      if (!lightModeOnlyPages.includes(currentPath)) {
        // Remove our forced light mode and let the theme context take over
        root.classList.remove("light");
        
        // Restore theme based on localStorage
        const theme = localStorage.getItem("arvalox-ui-theme") || "system";
        if (theme === "dark") {
          root.classList.add("dark");
        } else if (theme === "system") {
          const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
          root.classList.add(systemTheme);
        } else {
          root.classList.add("light");
        }
      }
    };
  }, []);

  return <div className="light">{children}</div>;
}