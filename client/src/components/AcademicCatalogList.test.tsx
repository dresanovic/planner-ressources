import {act} from 'react'
import {createRoot} from 'react-dom/client'
import {expect,it,vi} from 'vitest'
import {AcademicCatalogList} from './AcademicCatalogList'

it('exposes a keyboard button for copying each independent grouped record',()=>{
  const record={id:1,name:'Einmalig: 09.11.2026 · Intensivwoche',isActive:true,revision:1}
  const copy=vi.fn()
  const root=createRoot(document.body.appendChild(document.createElement('div')))
  act(()=>root.render(<AcademicCatalogList records={[record]} emptyLabel="Keine" groupBy={()=>'Einmalige Datumsfenster'} onCopy={copy}/>))
  const button=[...document.querySelectorAll('button')].find(b=>b.textContent==='Kopieren')!
  act(()=>{button.focus();button.click()})
  expect(copy).toHaveBeenCalledWith(record,button)
  expect(document.querySelector('section[aria-label="Einmalige Datumsfenster"]')).not.toBeNull()
})
