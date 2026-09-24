// Stand-in for the Claude runtime (window.claude) when the app runs outside Claude,
// served by server/server.js. Inside Claude the real runtime is kept untouched.
//  - sample: POST /api/suggest, where the server calls the Claude API with its own key
//  - db: the catalog comes from data/exercises.json, each person's record from localStorage
//  - user: a random id kept in localStorage
//  - assets: not needed, the server serves /_blob/<id> from assets/exercises/
(function(){
  if (window.claude) return;

  const store = {
    get(k){ try{ return JSON.parse(localStorage.getItem(k)); }catch(e){ return null; } },
    set(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)); }catch(e){} },
  };

  const snap = (id, data) => ({ id, exists: data != null, data: () => data });

  const db = {
    doc(p){
      const key = "digicoach:" + p;
      return {
        async get(){ return snap(p.split("/").pop(), store.get(key)); },
        async set(data){ store.set(key, data); },
        async update(data){ store.set(key, { ...(store.get(key) || {}), ...data }); },
      };
    },
    collection(name){
      return {
        async get(){
          if (name !== "ejercicios") return { docs: [] };
          const r = await fetch("/data/exercises.json");
          if (!r.ok) throw new Error("catalog " + r.status);
          const list = await r.json();
          return { docs: list.map(({ id, files, ...rest }) => snap(id, rest)) };
        },
      };
    },
  };

  const user = {
    async id(){
      let id = store.get("digicoach:uid");
      if (!id){ id = (crypto.randomUUID?.() || String(Math.random()).slice(2)); store.set("digicoach:uid", id); }
      return id;
    },
  };

  const sample = {
    async json(prompt, opts = {}){
      let r;
      try{
        r = await fetch("/api/suggest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt }),
          signal: opts.signal,
        });
      }catch(e){
        throw { code: e?.name === "AbortError" ? "cancelled" : "network" };
      }
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw { code: body.code || "api_error" };
      return body;
    },
  };

  const caps = { db, user, sample };
  window.claude = { use: async name => caps[name] || null };
})();
