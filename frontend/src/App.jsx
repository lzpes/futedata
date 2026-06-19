import { useState, useEffect } from 'react'
import { 
  Terminal, Play, Trash2, Database, Code2, GripVertical, Settings2, Moon, Sun, X, Activity, DollarSign, Target, User
} from 'lucide-react'
import './index.css'

const API_URL = 'http://localhost:8000/api'

// Mapeamento das colunas do SQL para Português
const COLUMN_LABELS = {
  "player_name": "Nome do Jogador",
  "age": "Idade",
  "position": "Posição",
  "nationality": "Nacionalidade",
  "club_name": "Clube",
  "squad_size": "Tamanho do Elenco",
  "market_value_in_eur": "Valor de Mercado (€)",
  "highest_market_value_in_eur": "Pico de Valorização (€)",
  "upside_value": "Potencial de Alta (€)",
  "total_goals": "Gols",
  "total_assists": "Assistências",
  "goal_contributions": "Participações em Gol",
  "total_minutes": "Minutos Jogados",
  "cost_per_contribution": "Custo por Participação (€)",
  "contributions_per_90": "Participações por 90 min",
  "contract_expiration_date": "Fim do Contrato"
}

const VW_MASTER_COLUMNS = Object.keys(COLUMN_LABELS)

const FILTER_OPS = ["=", ">", ">=", "<", "<=", "!=", "LIKE"]

function App() {
  // Theme State
  const [isDarkMode, setIsDarkMode] = useState(false)

  // Builder State
  const [builderColumns, setBuilderColumns] = useState(["player_name", "age", "club_name", "cost_per_contribution", "contributions_per_90"])
  const [builderFilters, setBuilderFilters] = useState([])
  const [showRawSql, setShowRawSql] = useState(false)

  // SQL State
  const [queryData, setQueryData] = useState([])
  const [queryColumns, setQueryColumns] = useState([])
  const [queryError, setQueryError] = useState(null)
  const [isQuerying, setIsQuerying] = useState(false)

  // Player Drawer State
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [playerDetails, setPlayerDetails] = useState(null)
  const [isPlayerLoading, setIsPlayerLoading] = useState(false)

  // Atualizar a classe do body baseada no tema
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('theme-dark')
    } else {
      document.body.classList.remove('theme-dark')
    }
  }, [isDarkMode])

  // Auto-compile SQL based on drag-and-drop state
  const compileSql = () => {
    let sql = `SELECT TOP 50\n  ${builderColumns.length > 0 ? builderColumns.join(',\n  ') : '*'}\nFROM vw_master_scout`
    
    if (builderFilters.length > 0) {
      const validFilters = builderFilters.filter(f => f.col && f.val !== '')
      if (validFilters.length > 0) {
        const conditions = validFilters.map(f => {
          let value = f.val
          if (f.op === "LIKE") {
            value = `'%${value}%'`
          } else if (isNaN(value)) {
            value = `'%${value}%'`
            if (f.op !== "=" && f.op !== "!=") return `${f.col} = '${value}'`
            return `${f.col} ${f.op} '${f.val}'`
          }
          return `${f.col} ${f.op} ${value}`
        })
        sql += `\nWHERE ` + conditions.join('\n  AND ')
      }
    }
    return sql
  }

  const [rawSqlInput, setRawSqlInput] = useState(compileSql())

  useEffect(() => {
    setRawSqlInput(compileSql())
  }, [builderColumns, builderFilters])

  // ================= DRAG AND DROP LOGIC =================
  const onDragStart = (e, col) => {
    e.dataTransfer.setData("col", col)
  }

  const onDragOver = (e) => {
    e.preventDefault() // Required to allow dropping
  }

  const onDropColumn = (e) => {
    e.preventDefault()
    const col = e.dataTransfer.getData("col")
    if (col && !builderColumns.includes(col)) {
      setBuilderColumns([...builderColumns, col])
    }
  }

  const onDropFilter = (e) => {
    e.preventDefault()
    const col = e.dataTransfer.getData("col")
    if (col) {
      setBuilderFilters([...builderFilters, { col, op: "=", val: "" }])
    }
  }

  const removeColumn = (colToRemove) => {
    setBuilderColumns(builderColumns.filter(c => c !== colToRemove))
  }

  const updateFilter = (index, field, value) => {
    const newFilters = [...builderFilters]
    newFilters[index][field] = value
    setBuilderFilters(newFilters)
  }

  const removeFilter = (index) => {
    setBuilderFilters(builderFilters.filter((_, i) => i !== index))
  }
  // =======================================================

  const runQuery = async () => {
    setIsQuerying(true)
    setQueryError(null)
    const finalSql = showRawSql ? rawSqlInput : compileSql()
    
    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: finalSql })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Erro na consulta")
      
      setQueryData(data.data)
      setQueryColumns(data.columns)
    } catch (err) {
      setQueryError(err.message)
      setQueryData([])
      setQueryColumns([])
    } finally {
      setIsQuerying(false)
    }
  }

  const openPlayerProfile = async (playerName) => {
    setIsDrawerOpen(true)
    setIsPlayerLoading(true)
    setPlayerDetails(null)
    
    try {
      const safeName = playerName.replace(/'/g, "''")
      const sql = `SELECT * FROM vw_master_scout WHERE player_name = '${safeName}'`
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: sql })
      })
      const data = await res.json()
      if (data.data && data.data.length > 0) {
        setPlayerDetails(data.data[0])
      }
    } catch (err) {
      console.error("Failed to load player details", err)
    } finally {
      setIsPlayerLoading(false)
    }
  }

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'N/A'
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(val)
  }

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <Database size={20} className="brand-icon" />
          <span className="brand-text">FuteData Studio</span>
        </div>
        <div className="nav-actions">
          <button 
            className="btn-outline" 
            onClick={() => setIsDarkMode(!isDarkMode)}
            title="Alternar Tema"
          >
            {isDarkMode ? <Sun size={14}/> : <Moon size={14}/>} {isDarkMode ? "Claro" : "Escuro"}
          </button>
          <button 
            className="btn-outline" 
            onClick={() => setShowRawSql(!showRawSql)}
          >
            <Code2 size={14}/> {showRawSql ? "Ocultar Editor SQL" : "Ver Editor SQL"}
          </button>
          <button 
            className="btn-primary" 
            onClick={runQuery} 
            disabled={isQuerying || builderColumns.length === 0}
          >
            {isQuerying ? <div className="spinner-small"></div> : <><Play size={14} /> Executar Consulta</>}
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="workspace">
        
        {/* Left Sidebar - Fields */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <Settings2 size={16} />
            <span>Métricas Disponíveis</span>
          </div>
          <div className="sidebar-list">
            {VW_MASTER_COLUMNS.map(col => (
              <div 
                key={col} 
                className="draggable-field"
                draggable
                onDragStart={(e) => onDragStart(e, col)}
              >
                <GripVertical size={14} className="drag-handle" />
                <span className="field-name">{COLUMN_LABELS[col]}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* Center Canvas - Builder & Results */}
        <section className="canvas-area">
          
          <div className="builder-zones">
            {/* Columns Zone */}
            <div 
              className="dropzone"
              onDragOver={onDragOver}
              onDrop={onDropColumn}
            >
              <div className="dropzone-header">Colunas da Tabela</div>
              {builderColumns.length === 0 ? (
                <div className="dropzone-placeholder">Arraste os campos aqui</div>
              ) : (
                <div className="pills-container">
                  {builderColumns.map(col => (
                    <div key={col} className="pill">
                      {COLUMN_LABELS[col]}
                      <Trash2 size={12} className="remove-icon" onClick={() => removeColumn(col)}/>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Filters Zone */}
            <div 
              className="dropzone"
              onDragOver={onDragOver}
              onDrop={onDropFilter}
            >
              <div className="dropzone-header">Regras de Filtro</div>
              {builderFilters.length === 0 ? (
                <div className="dropzone-placeholder">Arraste campos para criar filtros</div>
              ) : (
                <div className="filters-list">
                  {builderFilters.map((f, i) => (
                    <div key={i} className="filter-row">
                      <div className="filter-col-name">{COLUMN_LABELS[f.col]}</div>
                      <select className="input-select" value={f.op} onChange={(e) => updateFilter(i, 'op', e.target.value)}>
                        {FILTER_OPS.map(o => <option key={o} value={o}>{o}</option>)}
                      </select>
                      <input 
                        type="text" 
                        className="input-text" 
                        placeholder="Insira um valor..." 
                        value={f.val}
                        onChange={(e) => updateFilter(i, 'val', e.target.value)}
                      />
                      <button className="btn-icon-danger" onClick={() => removeFilter(i)}><Trash2 size={14}/></button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Raw SQL Editor Overlay (if active) */}
          {showRawSql && (
            <div className="sql-editor">
              <div className="editor-header">
                <Terminal size={14} /> SQL Equivalente (Apenas Leitura/Edição Manual)
              </div>
              <textarea 
                className="editor-textarea" 
                value={rawSqlInput}
                onChange={e => setRawSqlInput(e.target.value)}
                spellCheck={false}
              />
            </div>
          )}

          {/* Results Area */}
          <div className="results-area">
            {queryError && (
              <div className="alert-error">
                <strong>Erro na Consulta:</strong> {queryError}
              </div>
            )}

            {!queryError && queryData.length > 0 && (
              <div className="data-table-wrapper">
                <div className="table-header-info">
                  {queryData.length} registros encontrados
                </div>
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {queryColumns.map(col => <th key={col}>{COLUMN_LABELS[col] || col}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {queryData.map((row, rIdx) => (
                        <tr key={rIdx}>
                          {queryColumns.map(col => (
                            <td key={col}>
                              {col === 'player_name' ? (
                                <span className="clickable-player" onClick={() => openPlayerProfile(row[col])}>
                                  {row[col]}
                                </span>
                              ) : (
                                row[col] !== null ? row[col].toString() : <span className="null-val">nulo</span>
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {!queryError && queryData.length === 0 && !isQuerying && (
              <div className="empty-state">
                <Database size={32} />
                <p>Nenhum dado consultado. Arraste colunas e clique em "Executar Consulta".</p>
              </div>
            )}
          </div>
        </section>

      </main>

      {/* Player Profile Drawer */}
      <div className={`drawer-overlay ${isDrawerOpen ? 'open' : ''}`} onClick={() => setIsDrawerOpen(false)}>
        <div className={`drawer-panel ${isDrawerOpen ? 'open' : ''}`} onClick={e => e.stopPropagation()}>
          <div className="drawer-header-bar">
            <h3>Player Profile 360</h3>
            <button className="close-btn" onClick={() => setIsDrawerOpen(false)}><X size={20}/></button>
          </div>
          
          <div className="drawer-body">
            {isPlayerLoading && (
              <div className="drawer-loader">
                <div className="spinner"></div>
                <p>Analisando dados do atleta...</p>
              </div>
            )}

            {!isPlayerLoading && playerDetails && (
              <div className="profile-content">
                {/* Cabeçalho do Perfil */}
                <div className="profile-header">
                  {playerDetails.image_url ? (
                    <img src={playerDetails.image_url} alt={playerDetails.player_name} className="profile-photo" />
                  ) : (
                    <div className="profile-photo-placeholder"><User size={40} /></div>
                  )}
                  <div className="profile-title">
                    <h2>{playerDetails.player_name}</h2>
                    <p>{playerDetails.age} anos • {playerDetails.position} • {playerDetails.nationality}</p>
                    <p className="profile-club">{playerDetails.club_name}</p>
                  </div>
                </div>

                {/* Blocos de Dados */}
                <div className="profile-grid">
                  {/* Mercado */}
                  <div className="profile-card">
                    <div className="card-header"><DollarSign size={16}/> Mercado e Contrato</div>
                    <div className="card-stat">
                      <label>Valor Atual</label>
                      <span>{formatCurrency(playerDetails.market_value_in_eur)}</span>
                    </div>
                    <div className="card-stat">
                      <label>Pico Histórico</label>
                      <span>{formatCurrency(playerDetails.highest_market_value_in_eur)}</span>
                    </div>
                    <div className="card-stat">
                      <label>Upside (Potencial)</label>
                      <span className={playerDetails.upside_value > 0 ? "text-success" : ""}>
                        {formatCurrency(playerDetails.upside_value)}
                      </span>
                    </div>
                    <div className="card-stat">
                      <label>Vencimento Contrato</label>
                      <span>{playerDetails.contract_expiration_date || 'N/A'}</span>
                    </div>
                  </div>

                  {/* Eficiência */}
                  <div className="profile-card">
                    <div className="card-header"><Target size={16}/> Eficiência de Investimento</div>
                    <div className="card-stat">
                      <label>Custo por G/A</label>
                      <span>{formatCurrency(playerDetails.cost_per_contribution)}</span>
                    </div>
                    <div className="card-stat">
                      <label>G/A a cada 90 min</label>
                      <span>{playerDetails.contributions_per_90}</span>
                    </div>
                  </div>

                  {/* Performance */}
                  <div className="profile-card">
                    <div className="card-header"><Activity size={16}/> Performance em Campo</div>
                    <div className="card-stat">
                      <label>Total Gols</label>
                      <span>{playerDetails.total_goals}</span>
                    </div>
                    <div className="card-stat">
                      <label>Total Assistências</label>
                      <span>{playerDetails.total_assists}</span>
                    </div>
                    <div className="card-stat">
                      <label>Participações em Gol</label>
                      <span>{playerDetails.goal_contributions}</span>
                    </div>
                    <div className="card-stat">
                      <label>Minutos Jogados</label>
                      <span>{playerDetails.total_minutes}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {!isPlayerLoading && !playerDetails && (
              <div className="empty-state">
                <p>Jogador não encontrado no sistema.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
