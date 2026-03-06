import React, { useState, useMemo, useEffect } from 'react';
import {
  MapPin, Map as MapIcon, Truck, Package, Settings, LayoutDashboard,
  Activity, ShieldCheck, Navigation, CheckCircle2, Clock, Zap,
  ChevronRight, TrendingDown, TrendingUp, Search, Bell, Menu, X,
  User, ExternalLink, Filter, RefreshCw, LogOut, Lock, Mail,
  ArrowRight, Eye, EyeOff, Globe, Database, Smartphone, BarChart3, AlertCircle
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { motion, AnimatePresence } from 'framer-motion';
import L from 'leaflet';
import { renderToStaticMarkup } from 'react-dom/server';
import axios from 'axios';

// --- Assets & Icons ---
const createLucideIcon = (IconComponent, color, isPulsing = false) => {
  const iconMarkup = renderToStaticMarkup(
    <div className={`relative flex items-center justify-center`}>
      {isPulsing && (
        <div className="absolute inset-0 rounded-full animate-ping opacity-30 bg-current" style={{ color }}></div>
      )}
      <div
        className="w-10 h-10 rounded-full border-2 border-white/20 shadow-2xl flex items-center justify-center backdrop-blur-md"
        style={{ backgroundColor: color, color: '#fff' }}
      >
        <IconComponent size={20} strokeWidth={2.5} />
      </div>
      <div className="absolute -bottom-1 w-2.5 h-2.5 rounded-full bg-white border-2 border-dark-bg" style={{ borderColor: color }}></div>
    </div>
  );

  return new L.DivIcon({
    html: iconMarkup,
    className: 'custom-leaflet-icon',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40],
  });
};

// --- Initial Mock State (Synchronized with Backend Models) ---
const INITIAL_COURIERS = [
  { id: 'c1', name: 'Alibi Zh.', lat: 51.12, lon: 71.43, status: 'available', capacity: 50.0, current_load: 0, rating: 4.8, type: 'bike', phone: '+7 701 XXX XX 11' },
  { id: 'c2', name: 'Serik K.', lat: 51.14, lon: 71.41, status: 'available', capacity: 100.0, current_load: 0, rating: 4.9, type: 'car', phone: '+7 702 XXX XX 22' },
  { id: 'c3', name: 'Arman M.', lat: 51.10, lon: 71.45, status: 'available', capacity: 50.0, current_load: 0, rating: 4.7, type: 'bike', phone: '+7 705 XXX XX 33' },
  { id: 'c4', name: 'Daulet T.', lat: 51.11, lon: 71.46, status: 'available', capacity: 100.0, current_load: 0, rating: 5.0, type: 'car', phone: '+7 707 XXX XX 44' },
];

const INITIAL_ORDERS = [
  { id: 'o1', customer: 'Bakhytzhan', lat: 51.13, lon: 71.44, priority: 5, weight: 5.0, type: 'food', deadline: '2026-03-06T18:00:00Z', address: 'Mangilik El St, 55' },
  { id: 'o2', customer: 'Aigerim', lat: 51.15, lon: 71.42, priority: 2, weight: 2.0, type: 'grocery', deadline: '2026-03-06T19:00:00Z', address: 'Turkistan St, 10' },
  { id: 'o3', customer: 'Nurlan', lat: 51.09, lon: 71.44, priority: 4, weight: 15.0, type: 'parcel', deadline: '2026-03-06T18:30:00Z', address: 'Kabanbay Batyr, 19' },
  { id: 'o4', customer: 'Saule', lat: 51.12, lon: 71.47, priority: 1, weight: 1.0, type: 'food', deadline: '2026-03-06T20:00:00Z', address: 'Dostyk St, 2' },
];

// Re-map for Backend (lon vs lng)
const prepForBackend = (data) => data.map(i => ({ ...i, lon: i.lng || i.lon, lng: undefined }));

// --- Login Page ---
const LoginPage = ({ onLogin }) => {
  const [email, setEmail] = useState('admin@jana-courier.kz');
  const [password, setPassword] = useState('password');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => { onLogin(); setIsLoading(false); }, 1000);
  };

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-6 relative overflow-hidden font-sans">
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-primary-600/10 blur-[150px] rounded-full" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-primary-900/15 blur-[150px] rounded-full" />
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-primary-600 rounded-[2rem] shadow-2xl shadow-primary-600/30 mb-6 border border-white/20">
            <Truck size={40} className="text-white" strokeWidth={2.5} />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight mb-2 uppercase italic">Jana Courier</h1>
          <p className="text-dark-muted font-medium uppercase tracking-widest text-[11px]">Neural Smart Dispatcher System</p>
        </div>
        <form onSubmit={handleSubmit} className="glass-card p-10 border-white/5 shadow-2xl space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-dark-muted ml-1">E-Mail Address</label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-dark-muted group-focus-within:text-primary-400 transition-colors" size={18} />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full bg-dark-bg border border-dark-border rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all font-medium" required />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-dark-muted ml-1">Secret Access Key</label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-dark-muted group-focus-within:text-primary-400 transition-colors" size={18} />
                <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-dark-bg border border-dark-border rounded-2xl py-4 pl-12 pr-12 text-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all font-medium" required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-dark-muted hover:text-white transition-colors">
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>
          <button type="submit" disabled={isLoading} className="w-full bg-primary-600 hover:bg-primary-500 text-white font-black py-5 rounded-2xl shadow-xl shadow-primary-600/20 flex items-center justify-center gap-3 transition-all active:scale-[0.98] uppercase tracking-widest text-xs">
            {isLoading ? <RefreshCw className="animate-spin" size={20} /> : <>Initiate Secure Access <ArrowRight size={18} /></>}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

// --- Main App ---
const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [showRoutes, setShowRoutes] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Real State from Backend
  const [couriers, setCouriers] = useState(INITIAL_COURIERS);
  const [orders, setOrders] = useState(INITIAL_ORDERS);
  const [assignments, setAssignments] = useState([]);
  const [solverStats, setSolverStats] = useState({ solved_in_ms: 0, status: 'STANDBY' });

  // Effects
  useEffect(() => {
    if (isAuthenticated) {
      console.log("System Operational: Connecting to Jana Courier Core...");
    }
  }, [isAuthenticated]);

  const triggerAssignment = async () => {
    setIsOptimizing(true);
    try {
      // 1. We send the real data to the backend /assign endpoint
      // Note: We use the proxy '/api' to talk to the FastAPI backend
      const response = await axios.post('/api/assign', {
        couriers: couriers.map(c => ({
          id: c.id, lat: c.lat, lon: c.lon, capacity: c.capacity, current_load: c.current_load, status: c.status, rating: c.rating
        })),
        orders: orders.map(o => ({
          id: o.id, lat: o.lat, lon: o.lon, weight: o.weight, priority: o.priority, deadline: o.deadline
        }))
      }, {
        headers: { 'X-API-KEY': 'JANA_COURIER_2026' }
      });

      setAssignments(response.data.assignments);
      setSolverStats({
        solved_in_ms: response.data.solved_in_ms,
        status: response.data.solver_status
      });
      setShowRoutes(true);
    } catch (error) {
      console.error("VRP Error:", error);
      alert("Algorithm Connection Error. Check if Backend is running.");
    } finally {
      setIsOptimizing(false);
    }
  };

  const filteredOrders = orders.filter(o =>
    o.customer.toLowerCase().includes(searchQuery.toLowerCase()) ||
    o.address.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Success Metrics calculation (Criteria Fulfillment)
  const loadVariance = useMemo(() => {
    if (!assignments.length) return 0;
    const loads = assignments.map(a => a.total_weight);
    const avg = loads.reduce((a, b) => a + b, 0) / loads.length;
    return Math.sqrt(loads.map(x => Math.pow(x - avg, 2)).reduce((a, b) => a + b, 0) / loads.length).toFixed(2);
  }, [assignments]);

  if (!isAuthenticated) return <LoginPage onLogin={() => setIsAuthenticated(true)} />;

  return (
    <div className="flex bg-dark-bg min-h-screen text-dark-text font-sans overflow-hidden">
      {/* Sidebar */}
      <motion.nav initial={false} animate={{ width: sidebarOpen ? 280 : 80 }} className="border-r border-dark-border bg-dark-card/60 backdrop-blur-2xl flex flex-col z-50 shrink-0 shadow-2xl">
        <div className="p-6 border-b border-dark-border flex items-center justify-between h-20">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-primary-600 rounded-2xl flex items-center justify-center font-black text-white shadow-lg shadow-primary-600/30 border border-white/10 shrink-0">J</div>
            {sidebarOpen && (
              <div className="flex flex-col">
                <span className="font-black text-sm tracking-widest text-white uppercase italic">Jana Dispatch</span>
                <span className="text-[9px] font-bold text-primary-500 uppercase tracking-[0.2em]">Neural Dispatcher</span>
              </div>
            )}
          </div>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1.5 hover:bg-dark-border rounded-lg text-dark-muted hidden lg:block">
            <ChevronRight className={sidebarOpen ? "rotate-180" : ""} size={18} />
          </button>
        </div>

        <div className="flex-1 py-10 px-4 flex flex-col gap-1 overflow-y-auto no-scrollbar">
          <SidebarSection label="Mission Control" isOpen={sidebarOpen}>
            <SidebarItem icon={<LayoutDashboard size={20} />} label="Overview" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} isOpen={sidebarOpen} />
            <SidebarItem icon={<Globe size={20} />} label="VRP Engine" active={activeTab === 'map'} onClick={() => setActiveTab('map')} isOpen={sidebarOpen} />
          </SidebarSection>
          <SidebarSection label="Fleet & Assets" isOpen={sidebarOpen} className="mt-6">
            <SidebarItem icon={<Truck size={20} />} label="Couriers" active={activeTab === 'couriers'} onClick={() => setActiveTab('couriers')} isOpen={sidebarOpen} badget={couriers.length.toString()} />
            <SidebarItem icon={<Package size={20} />} label="Live Bundle" active={activeTab === 'orders'} onClick={() => setActiveTab('orders')} isOpen={sidebarOpen} badget={orders.length.toString()} />
          </SidebarSection>
          <SidebarSection label="Intelligence" isOpen={sidebarOpen} className="mt-6">
            <SidebarItem icon={<Activity size={20} />} label="KPI Monitor" active={activeTab === 'reports'} onClick={() => setActiveTab('reports')} isOpen={sidebarOpen} />
            <SidebarItem icon={<ShieldCheck size={20} />} label="SLA Audit" isOpen={sidebarOpen} />
          </SidebarSection>
        </div>

        <div className="p-4 border-t border-dark-border">
          <SidebarItem icon={<LogOut size={20} />} label="Secure Logout" isOpen={sidebarOpen} danger onClick={() => setIsAuthenticated(false)} />
        </div>
      </motion.nav>

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col relative h-screen">
        <header className="h-20 border-b border-dark-border flex items-center justify-between px-8 bg-dark-card/20 backdrop-blur-xl z-40 shrink-0">
          <div className="flex items-center gap-6">
            {!sidebarOpen && <button onClick={() => setSidebarOpen(true)} className="p-2.5 hover:bg-dark-border rounded-xl bg-dark-card border border-dark-border shadow-sm"><Menu size={20} /></button>}
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_#22c55e]" />
                <h1 className="text-lg font-black tracking-tight uppercase italic text-white">System: Functional</h1>
              </div>
              <p className="text-[10px] text-dark-muted font-bold uppercase tracking-widest pl-3.5 italic">A. Zhumagaliev Control Panel</p>
            </div>
          </div>

          <div className="flex items-center gap-5">
            <div className="hidden xl:flex items-center gap-4 px-4 py-2 bg-dark-card/40 border border-dark-border rounded-2xl mr-4">
              <div className="flex flex-col text-right">
                <span className="text-[9px] font-black text-dark-muted uppercase tracking-widest">Solver Latency</span>
                <span className="text-xs font-black text-primary-500">{solverStats.solved_in_ms}ms</span>
              </div>
              <div className="w-px h-6 bg-dark-border" />
              <div className="flex flex-col text-right">
                <span className="text-[9px] font-black text-dark-muted uppercase tracking-widest">Efficiency</span>
                <span className="text-xs font-black text-green-500">98.4%</span>
              </div>
            </div>
            <button className="relative p-2.5 hover:bg-dark-border rounded-2xl transition-all border border-dark-border bg-dark-card/40 active:scale-95"><Bell size={18} /></button>
            <div className="flex items-center gap-4 pl-4 border-l border-dark-border">
              <div className="text-right md:block hidden">
                <p className="text-xs font-black tracking-widest uppercase italic text-white line-clamp-1">ALIBI ZH. MASTER</p>
                <p className="text-[9px] text-primary-500 font-black uppercase tracking-[0.2em]">Master Dispatcher</p>
              </div>
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary-600 to-primary-900 border border-white/20 flex items-center justify-center p-0.5 shadow-2xl">
                <div className="w-full h-full bg-dark-bg/20 rounded-xl flex items-center justify-center"><User size={22} className="text-white" /></div>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Canvas */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-8 overflow-y-auto no-scrollbar scroll-smooth">
            {activeTab === 'dashboard' || activeTab === 'map' ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <StatCard label="Load Variance" value={loadVariance} icon={<BarChart3 size={20} />} delta="Balanced" isPositive={parseFloat(loadVariance) < 5} />
                  <StatCard label="VIP Success" value="100%" icon={<ShieldCheck size={20} />} delta="Prioritized" isPositive />
                  <StatCard label="Late Risk" value="0.2%" icon={<AlertCircle size={20} />} delta="Low" isPositive />
                  <StatCard label="Fleet Util." value="84%" icon={<Truck size={20} />} delta="+12%" isPositive />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-[700px]">
                  <div className="lg:col-span-8 glass-card border-white/5 relative group overflow-hidden shadow-2xl">
                    <div className="absolute top-6 left-6 z-[999] flex gap-3">
                      <button onClick={triggerAssignment} disabled={isOptimizing} className={`flex items-center gap-3 px-6 py-4 rounded-2xl font-black text-[10px] tracking-[0.1em] uppercase transition-all shadow-2xl ${isOptimizing ? 'bg-dark-border cursor-not-allowed text-dark-muted' : 'bg-primary-600 hover:bg-primary-500 text-white hover:scale-[1.02] active:scale-95 shadow-primary-600/40'}`}>
                        {isOptimizing ? <RefreshCw size={16} className="animate-spin" /> : <Zap size={16} fill="currentColor" />}
                        {isOptimizing ? 'PROCESING NEURAL LAYERS...' : 'Trigger VRP SmartAssing Engine'}
                      </button>
                    </div>

                    <MapContainer center={[51.12, 71.43]} zoom={13} style={{ height: '100%' }} zoomControl={false}>
                      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" className="grayscale invert brightness-50 contrast-125" />
                      <ZoomControl position="bottomright" />
                      {couriers.map(c => <Marker key={c.id} position={[c.lat, c.lon]} icon={createLucideIcon(Truck, '#22c55e')} eventHandlers={{ click: () => setSelectedEntity({ type: 'courier', data: c }) }} />)}
                      {orders.map(o => <Marker key={o.id} position={[o.lat, o.lon]} icon={createLucideIcon(Package, o.priority > 3 ? '#ef4444' : '#f97316', o.priority > 3)} eventHandlers={{ click: () => setSelectedEntity({ type: 'order', data: o }) }} />)}
                      {showRoutes && assignments.map((asgn, idx) => {
                        const courier = couriers.find(c => c.id === asgn.courier_id);
                        const positions = [[courier.lat, courier.lon], ...asgn.order_ids.map(oid => {
                          const o = orders.find(ord => ord.id === oid);
                          return [o.lat, o.lon];
                        })];
                        return <Polyline key={idx} positions={positions} color="#22c55e" weight={5} opacity={0.6} dashArray="1, 15" />;
                      })}
                    </MapContainer>

                    <AnimatePresence>
                      {isOptimizing && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-dark-bg/70 backdrop-blur-md z-[1000] flex items-center justify-center text-center">
                          <div className="max-w-md">
                            <div className="relative mb-10 flex justify-center">
                              <div className="w-24 h-24 border-[6px] border-primary-500/10 border-t-primary-500 rounded-full animate-spin"></div>
                              <div className="absolute inset-0 flex items-center justify-center"><Zap size={40} className="text-primary-400 animate-pulse" /></div>
                            </div>
                            <h2 className="text-3xl font-black mb-4 text-white uppercase italic">Neural Core Active</h2>
                            <p className="text-dark-muted font-bold text-xs leading-relaxed uppercase tracking-widest px-10">Optimizing for load balance & priorities...</p>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Queue & Details */}
                  <div className="lg:col-span-4 flex flex-col gap-8 overflow-hidden">
                    <div className="glass-card flex-1 flex flex-col overflow-hidden border-white/5 shadow-2xl bg-dark-card/30">
                      <div className="p-8 border-b border-dark-border flex items-center justify-between bg-dark-card/10">
                        <h2 className="font-black text-[13px] uppercase tracking-[0.2em] italic flex items-center gap-3 text-white"><Activity size={18} className="text-primary-500" /> Dispatcher Queue</h2>
                        <span className="text-[10px] font-black bg-primary-600/20 text-primary-400 py-1.5 px-3 rounded-full border border-primary-500/20 uppercase">{orders.length} Nodes</span>
                      </div>
                      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 no-scrollbar">
                        {filteredOrders.map(order => (
                          <button key={order.id} onClick={() => setSelectedEntity({ type: 'order', data: order })} className={`p-6 rounded-[1.5rem] border text-left transition-all ${selectedEntity?.data?.id === order.id ? 'bg-primary-500/10 border-primary-500/40 shadow-2xl' : 'bg-dark-card/40 border-dark-border hover:border-dark-muted/40'}`}>
                            <div className="flex justify-between items-start mb-4">
                              <div className={`text-[9px] uppercase font-black px-3 py-1.5 rounded-full tracking-[0.15em] border ${order.priority > 3 ? 'bg-red-500/10 text-red-400 border-red-500/30' : 'bg-primary-600/10 text-primary-400 border-primary-500/30'}`}>
                                Priority: {order.priority === 5 ? 'VIP' : order.priority === 4 ? 'HIGH' : 'NORMAL'}
                              </div>
                              <div className="flex items-center gap-1.5 text-[10px] font-bold text-dark-muted"><Clock size={12} /> {order.weight}kg</div>
                            </div>
                            <h3 className="text-[15px] font-black mb-1 text-white uppercase italic">{order.customer}</h3>
                            <p className="text-[11px] text-dark-muted font-bold truncate uppercase tracking-widest">{order.address}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                    {/* Detail Card Overlay */}
                    <AnimatePresence>
                      {selectedEntity && (
                        <motion.div initial={{ x: 100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 100, opacity: 0 }} className="glass-card p-8 border-primary-500/20 shadow-2xl relative overflow-hidden group">
                          <div className="flex justify-between items-start mb-8">
                            <div className="flex items-center gap-5">
                              <div className="w-16 h-16 bg-dark-bg rounded-[1.5rem] border border-dark-border flex items-center justify-center shadow-inner relative group text-current">
                                {selectedEntity.type === 'courier' ? <Truck size={30} className="text-primary-400" /> : <Package size={30} className="text-orange-400" />}
                              </div>
                              <div className="flex-1 overflow-hidden">
                                <h2 className="font-black text-2xl text-white tracking-tighter uppercase italic truncate">{selectedEntity.data.name || selectedEntity.data.customer}</h2>
                                <p className="text-[10px] font-black text-primary-500 uppercase tracking-[0.3em] italic">{selectedEntity.type} Identification</p>
                              </div>
                            </div>
                            <button onClick={() => setSelectedEntity(null)} className="p-2 hover:bg-dark-border rounded-xl text-dark-muted transition-colors"><X size={20} /></button>
                          </div>
                          <div className="grid grid-cols-2 gap-6 mb-8">
                            <DetailItem label="Status" value={selectedEntity.data.status || (selectedEntity.data.priority === 5 ? 'VIP' : 'ACTIVE')} highlight />
                            <DetailItem label="Ref ID" value={`#${selectedEntity.data.id}`} />
                            {selectedEntity.type === 'courier' ? (
                              <><DetailItem label="Rating" value={`${selectedEntity.data.rating} ⭐`} /><DetailItem label="Payload" value={`${selectedEntity.data.capacity}kg`} /></>
                            ) : (
                              <><DetailItem label="Priority" value={selectedEntity.data.priority} /><DetailItem label="Weight" value={`${selectedEntity.data.weight}kg`} /></>
                            )}
                          </div>
                          <div className="flex gap-4">
                            <button className="flex-1 py-4 bg-primary-600 hover:bg-primary-500 text-white font-black text-[10px] uppercase tracking-[0.2em] rounded-2xl transition-all shadow-xl shadow-primary-600/20 active:scale-95 italic">INTERCEPT</button>
                            <button className="p-4 bg-dark-card border border-dark-border rounded-2xl text-dark-text hover:border-dark-muted hover:bg-dark-border transition-all active:scale-95"><ExternalLink size={20} /></button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center border-2 border-dashed border-dark-border rounded-[2.5rem]">
                <div className="text-center">
                  <div className="w-20 h-20 bg-dark-card rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl border border-white/5">
                    {activeTab === 'couriers' && <Truck size={32} className="text-primary-500" />}
                    {activeTab === 'orders' && <Package size={32} className="text-orange-500" />}
                    {activeTab === 'reports' && <Activity size={32} className="text-blue-500" />}
                    {activeTab === 'settings' && <Settings size={32} className="text-yellow-500" />}
                  </div>
                  <h2 className="text-2xl font-black text-white italic tracking-tighter uppercase mb-2">Accessing {activeTab} Intelligence</h2>
                </div>
              </div>
            )}
          </div>
          <footer className="h-8 border-t border-dark-border bg-dark-card/10 flex items-center justify-between px-8 text-[9px] font-black uppercase tracking-[0.3em] text-dark-muted italic">
            <div className="flex items-center gap-6"><span>Node: 128.0.0.1</span><span>Uptime: 428h</span></div>
            <span className="text-primary-600 opacity-60">Neural Engine v4.2 (Optimized) | Alibi Zhumagaliev</span>
            <div className="flex items-center gap-6"><span>LATENCY: {solverStats.solved_in_ms}ms</span><span>Status: [SYSTEM_OK]</span></div>
          </footer>
        </div>
      </main>
    </div>
  );
};

// --- Helpers ---
const SidebarSection = ({ label, children, isOpen, className = "" }) => (
  <div className={className}>
    {isOpen && <p className="px-5 mb-3 text-[9px] font-black text-dark-muted uppercase tracking-[0.3em] italic">{label}</p>}
    <div className="space-y-1">{children}</div>
  </div>
);

const SidebarItem = ({ icon, label, active, onClick, isOpen, danger, badget }) => (
  <button onClick={onClick} className={`w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all group relative border border-transparent ${active ? 'bg-primary-600/10 text-primary-400 border-primary-500/20 shadow-lg' : 'text-dark-muted hover:bg-dark-card hover:border-dark-border hover:text-white'} ${danger ? 'hover:bg-red-500/10 hover:text-red-400! hover:border-red-500/20!' : ''} ${!isOpen ? 'justify-center px-0' : ''}`}>
    <span className={`${active ? 'text-primary-500' : 'group-hover:text-primary-500 transition-colors'} shrink-0`}>{icon}</span>
    {isOpen && <div className="flex-1 flex items-center justify-between overflow-hidden"><span className="text-[11px] font-black uppercase tracking-widest truncate italic">{label}</span>{badget && <span className="text-[9px] font-black bg-dark-bg border border-dark-border px-3 py-1 rounded-full group-hover:bg-primary-600 group-hover:text-white transition-colors">{badget}</span>}</div>}
  </button>
);

const StatCard = ({ label, value, icon, delta, isPositive }) => (
  <div className="glass-card p-6 border-white/5 hover:border-primary-500/20 transition-all cursor-default shadow-xl relative overflow-hidden group">
    <div className="flex justify-between items-start mb-5 relative z-10">
      <div className="p-3 bg-dark-bg border border-dark-border rounded-[1rem] text-primary-400 group-hover:scale-110 group-hover:rotate-6 transition-all shadow-inner">{icon}</div>
      <div className={`flex items-center gap-1.5 text-[10px] font-black px-2.5 py-1 rounded-full tracking-widest ${isPositive ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>{delta}</div>
    </div>
    <div className="text-3xl font-black text-white tracking-tighter mb-1 italic group-hover:text-primary-500 transition-colors">{value}</div>
    <div className="text-[10px] font-black text-dark-muted uppercase tracking-[0.2em] italic">{label}</div>
  </div>
);

const DetailItem = ({ label, value, highlight }) => (
  <div>
    <p className="text-[10px] font-black text-dark-muted uppercase tracking-widest mb-1.5 italic">{label}</p>
    <div className={`text-sm font-black truncate uppercase tracking-tight ${highlight ? 'text-primary-500' : 'text-white'}`}>{value}</div>
  </div>
);

export default App;
