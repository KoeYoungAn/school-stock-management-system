import React from 'react'
import MasterDataPage from './_MasterDataPage.jsx'
import { required, minLength, email } from '../utils/validation.js'

const supplierSchema = {
  supplier_name: [required('Supplier Name'), minLength(2, 'Supplier Name')],
  email: [email('Email')]
}

export default function Suppliers() {
  return <MasterDataPage
    base="/api/suppliers" title={{ key:'supplier', newKey:'newSupplier', editKey:'editSupplier', emptyKey:'noSuppliers' }} nameKey="supplier_name"
    blankForm={{ supplier_name:'', contact_person:'', email:'', phone:'', address:'', status:'Active', notes:'' }}
    fields={[
      { name:'supplier_name', labelKey:'supplierName', required:true },
      { name:'contact_person', labelKey:'contactPerson' },
      { name:'email', labelKey:'email', type:'email' },
      { name:'phone', labelKey:'phone' },
      { name:'address', labelKey:'address', type:'textarea' },
      { name:'status', labelKey:'status', type:'select', options:['Active','Inactive'] },
      { name:'notes', labelKey:'notes', type:'textarea' },
    ]}
    columns={[
      { key:'supplier_name', labelKey:'name' },
      { key:'contact_person', labelKey:'contact' },
      { key:'email', labelKey:'email' },
      { key:'phone', labelKey:'phone' },
    ]}
    validationSchema={supplierSchema}
  />
}
