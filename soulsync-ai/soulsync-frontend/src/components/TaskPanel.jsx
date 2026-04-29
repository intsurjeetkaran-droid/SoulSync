import { useState, useEffect } from "react";
import { CheckSquare, Plus, Trash2, Check,
         Clock, AlertCircle, Loader2, ListTodo } from "lucide-react";
import { getTasks, createTask, completeTask, deleteTask } from "../api/soulsync";
import toast from "react-hot-toast";

const PRIORITY = {
  high  : { text: "text-red-400",   bg: "bg-red-400/10",   border: "border-red-400/20",   icon: <AlertCircle size={10} /> },
  medium: { text: "text-glow-400",  bg: "bg-glow-400/10",  border: "border-glow-400/20",  icon: <Clock size={10} /> },
  low   : { text: "text-soul-400",  bg: "bg-soul-400/10",  border: "border-soul-400/20",  icon: <Check size={10} /> },
};

export default function TaskPanel({ userId, refreshTrigger }) {
  const [tasks,    setTasks]    = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [adding,   setAdding]   = useState(false);
  const [showForm, setShowForm] = useState(false);

  const fetchTasks = async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const res = await getTasks(userId);
      setTasks(res.data.tasks || []);
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchTasks(); }, [userId, refreshTrigger]);

  const handleAdd = async () => {
    if (!newTitle.trim()) return;
    setAdding(true);
    try {
      await createTask(userId, newTitle.trim(), null, "medium");
      setNewTitle(""); setShowForm(false);
      toast.success("Task created!");
      fetchTasks();
    } catch { toast.error("Failed to create task"); }
    finally { setAdding(false); }
  };

  const handleComplete = async (id) => {
    try {
      await completeTask(id, userId);
      toast.success("Done! 🎉");
      fetchTasks();
    } catch { toast.error("Failed to update"); }
  };

  const handleDelete = async (id) => {
    try {
      await deleteTask(id, userId);
      fetchTasks();
    } catch { toast.error("Failed to delete"); }
  };

  const pending   = tasks.filter(t => t.status === "pending");
  const completed = tasks.filter(t => t.status === "completed");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ListTodo size={15} className="text-soul-400" />
          <span className="text-sm font-semibold text-white">Tasks</span>
          {pending.length > 0 && (
            <span className="badge-emerald">{pending.length}</span>
          )}
        </div>
        <button onClick={() => setShowForm(v => !v)}
          className={`p-1.5 rounded-lg transition-all duration-200
                      ${showForm
                        ? "bg-soul-600/20 text-soul-400"
                        : "hover:bg-surface-800 text-surface-500 hover:text-soul-400"}`}>
          <Plus size={15} />
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="mb-3 flex gap-2 animate-slide-up">
          <input
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAdd()}
            placeholder="New task…"
            className="input-field text-xs py-2"
            autoFocus
          />
          <button onClick={handleAdd} disabled={adding}
            className="btn-primary text-xs px-3 py-2 shrink-0">
            {adding ? <Loader2 size={13} className="animate-spin" /> : "Add"}
          </button>
        </div>
      )}

      {/* List */}
      <div className="flex-1 overflow-y-auto space-y-1.5">
        {loading && (
          <div className="flex justify-center py-6">
            <Loader2 size={17} className="animate-spin text-soul-500" />
          </div>
        )}

        {!loading && pending.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <CheckSquare size={24} className="text-surface-700" />
            <p className="text-xs text-surface-600">No pending tasks</p>
          </div>
        )}

        {pending.map(task => {
          const p = PRIORITY[task.priority] || PRIORITY.medium;
          return (
            <div key={task.id}
              className="group flex items-start gap-2.5 p-3 rounded-xl
                         bg-surface-800/60 border border-surface-700/50
                         hover:border-surface-600/70 hover:bg-surface-800
                         transition-all duration-200">
              {/* Checkbox */}
              <button onClick={() => handleComplete(task.id)}
                className="w-4 h-4 rounded border border-surface-600
                           hover:border-soul-500 hover:bg-soul-600/20
                           flex items-center justify-center shrink-0 mt-0.5
                           transition-all duration-200 group/cb">
                <Check size={9} className="text-transparent group-hover/cb:text-soul-400" />
              </button>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-xs text-surface-200 leading-snug">{task.title}</p>
                <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                  <span className={`inline-flex items-center gap-0.5 text-[10px]
                                    px-1.5 py-0.5 rounded-full border font-medium
                                    ${p.text} ${p.bg} ${p.border}`}>
                    {p.icon} {task.priority}
                  </span>
                  {task.due_date && (
                    <span className="text-[10px] text-surface-500 flex items-center gap-0.5">
                      <Clock size={9} /> {task.due_date}
                    </span>
                  )}
                  {task.source === "auto" && (
                    <span className="text-[10px] text-soul-500/70 italic">auto</span>
                  )}
                </div>
              </div>

              {/* Delete */}
              <button onClick={() => handleDelete(task.id)}
                className="opacity-0 group-hover:opacity-100 p-1 rounded
                           hover:bg-red-500/10 text-surface-600 hover:text-red-400
                           transition-all duration-200 shrink-0">
                <Trash2 size={11} />
              </button>
            </div>
          );
        })}

        {/* Completed */}
        {completed.length > 0 && (
          <div className="mt-4 pt-3 border-t border-surface-800">
            <p className="text-[11px] text-surface-600 mb-2 font-medium uppercase tracking-wider">
              Completed · {completed.length}
            </p>
            {completed.slice(0, 4).map(task => (
              <div key={task.id}
                className="flex items-center gap-2 py-1.5 px-1 opacity-40">
                <Check size={11} className="text-soul-500 shrink-0" />
                <p className="text-xs text-surface-400 line-through truncate">{task.title}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
