import React from 'react';
import { Globals } from './interfaces';
import { Route, Routes, Outlet } from 'react-router-dom';
import ToolsHome from './components/ToolsHome';
import AltTextHome from './components/AltTextHome';
import HeaderAppBar from './components/HeaderAppBar';
import AltTextReview from './components/AltTextReview';


interface AppProps {
  globals: Globals
}

function AltTextLayout({ globals }: { globals: Globals }) {
  return (
    <>
      <HeaderAppBar
        breadcrumbTitle='Alt Text Helper'
        user={globals.user}
        helpURL={globals.help_url}
      />
      <Outlet />
    </>
  );
}

function App (props: AppProps) {

  return (
    <div id='root'>
      <Routes>
          <Route path='/' element={
            <ToolsHome {...props} />
          }/>
          <Route path='alt-text-helper' element={
            <AltTextLayout globals={props.globals} />
          }>
            <Route index element={<AltTextHome {...props}/>} />
            <Route path='review' element={<AltTextReview />} />
          </Route>
      </Routes>
    </div>
  );
}
export default App;