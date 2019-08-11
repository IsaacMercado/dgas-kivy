from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.network.urlrequest import UrlRequest
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image

from datetime import datetime, timedelta
import urllib.parse, json, sqlite3, pytz, os, re

NAME_DATABASE = 'database.db'
URL_HOST = 'http://127.0.0.1:8000/'
URL_ENDPOINT = URL_HOST+'api/cola/'
URL_TOKEN = URL_HOST + 'api-token-auth/'
DAYS_COUNT = 4
SOURCE_CHECK = 'images/check.png'
SOURCE_FAIL = 'images/mark.png'

def popup_view_alert(text, button_text, title=''):
    layout = GridLayout(cols=1, padding=10)
    closeButton = Button(text = button_text)
    layout.add_widget(Label(text = text))
    layout.add_widget(closeButton)
    popup = Popup(title=title, content=layout)
    popup.open()   
    closeButton.bind(on_press=popup.dismiss)
    return popup

def modal_view_alert(text, button_text='Cerrar', image=None):
    view = ModalView(size_hint=(None, None), size=(400, 400))
    layout = GridLayout(cols=1, padding=10)
    content = Button(
        text=button_text, 
        size_hint=(None, None), 
        size=(380, 100),
        valign= 'center')

    if image:
        layout.add_widget(image)
    layout.add_widget(Label(text=text))
    layout.add_widget(content)
    view.add_widget(layout)
    content.bind(on_press=view.dismiss)
    view.open()
    return view


class Display(BoxLayout):
    def __init__(self, *arg):
        super().__init__(*arg)
        conn = sqlite3.connect(NAME_DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS cola \
                ("id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, \
                 estacion INTEGER, placa TEXT, created_at DATETIME, estado BOOL, up BOOL);')
            cur.execute('CREATE TABLE IF NOT EXISTS estacion \
                (id INTEGER NOT NULL PRIMARY KEY, nombre TEXT);')
            cur.execute('CREATE TABLE IF NOT EXISTS updates \
                ("id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
                 update_date DATETIME);')
            cur.execute('DELETE FROM cola WHERE created_at < "%s";' % (datetime.now()-timedelta(days=DAYS_COUNT)).isoformat())
            cur.execute('SELECT * FROM estacion;')
            rows = cur.fetchall()
            if rows:
                self.ids.sm.get_screen("screen_list").ids.spinner_station.values = [nombre for _, nombre in rows]
        conn.close()

    def get_screen_login(self):
        app = App.get_running_app()
        if app.is_login:
            self.ids.sm.current = 'connected'
        else:
            self.ids.sm.current = 'screen_login'

class Connected(Screen):
    def disconnect(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'screen_login'
        self.manager.get_screen('screen_login').resetForm()

        app = App.get_running_app()
        app.is_login = False
        app.api_token = None

class PlacaInput(TextInput):
    pat = re.compile(r'[^0-9A-Z]')
    def insert_text(self, substring, from_undo=False):
        s = ''
        if not len(self.text) > 10:
            s = self.pat.sub('', substring[:10].upper())
        return super(PlacaInput, self).insert_text(s, from_undo=from_undo)

class Screen_Login(Screen):
    def do_login(self, loginText, passwordText):

        app = App.get_running_app()

        def login_in(req, result):
            app.username = loginText
            app.password = passwordText
            app.is_login = True
            app.api_token = result['token']

            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = 'connected'

            app.config.read(app.get_application_config())
            app.config.write()
            
            modal_view_alert('Esta loggeado','Cerrar',
                Image(source=SOURCE_CHECK, size=(100,100)))

        def fail_login(req, result):
            modal_view_alert('Error de conexión...\nReintente mas tarde','Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        def error_login(req, error):
            modal_view_alert('¡Error!','Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        req = UrlRequest(URL_TOKEN, on_success=login_in, on_error=error_login, on_failure=fail_login,
            req_headers = {'Content-type': 'application/json'},
            req_body=json.dumps({'username':loginText, 'password': passwordText}))
        

    def resetForm(self):
        self.ids['login'].text = ""
        self.ids['password'].text = ""

class Screen_Search(Screen):
    def onButtonPress(self, text):
        conn = sqlite3.connect(NAME_DATABASE)
        text_send = '¡Puede cargar!'
        with conn:
            cur = conn.cursor()
            last_date = datetime.now()-timedelta(days=DAYS_COUNT)
            cur.execute('SELECT estacion.nombre, cola.created_at FROM cola, estacion WHERE cola.placa = "%s" AND cola.estacion = estacion.id AND cola.created_at > "%s";' % (text, last_date.isoformat()))
            rows = cur.fetchall()

            if rows:
                sta, cda = rows.pop()
                text_send = "Ya cargo el %s, \nen la estación de servicio %s" % (datetime.strptime(cda, "%Y-%m-%dT%H:%M:%S.%f").ctime(), sta)

        conn.close()
        modal_view_alert(text_send, 'Cerrar', 
            Image(source=SOURCE_CHECK, size=(100,100)))


class Screen_List(Screen):

    def onButtonResponse(self, text, station):

        conn = sqlite3.connect(NAME_DATABASE)
        cstation = None
        cargo = False
        date  = None
        text_send = None

        with conn:
            cur = conn.cursor()
            last_date = datetime.now()-timedelta(days=DAYS_COUNT)
            cur.execute('SELECT estacion.nombre, cola.created_at FROM cola, estacion WHERE cola.placa = "%s" AND cola.estacion = estacion.id AND cola.created_at > "%s";' % (text, last_date.isoformat()))
            rows = cur.fetchall()

            if rows:
            	cargo = True
            	cstation, cdate = rows.pop()
            	date = datetime.strptime(cdate, "%Y-%m-%dT%H:%M:%S.%f")

            cur.execute('SELECT * FROM estacion WHERE nombre = "%s"' % station)
            rows = cur.fetchall()
            if rows:
                #print('in_')
                id_estacion, nombre = rows.pop()
                cur.execute('INSERT INTO cola VALUES (NULL, "%s", "%s", "%s", %i, %i);' % (id_estacion, 
                    text, datetime.now().isoformat(), cargo, False))
            else:
                text_send = '!Error al cargar!,\n no a selecciondado alguna estación o\n no a sincronizado los datos de las estaciones.'


        conn.close()

        source_image = SOURCE_FAIL

        if text_send:
            text_send = text_send
        elif cargo:
            text_send = ("Ya ha cargado el %s en la estación \nde servicio %s, será rebotado le toca volver a \n" +\
                         "cargar después del %s") % (date.ctime(), cstation, (date+timedelta(days=DAYS_COUNT)).ctime())
        else:
            source_image = SOURCE_CHECK
            text_send = "Ya cargo con exito, le toca volver \na cargar el %s" % (datetime.now()+timedelta(days=DAYS_COUNT)).ctime()

        modal_view_alert(text_send, 'Continuar', 
            Image(source=source_image, size=(100,100)))


class Screen_Sync(Screen):

    date_update = None

    def syncron_stations(self):

        app = App.get_running_app()
        
        if not app.is_login:
            return modal_view_alert('No esta loggeado para \nhacer esta acción', 'Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        def progress_stations(request, current_size, total_size):
            label.text = "Cargando " + str(round(current_size*100/total_size)) + "%"

        def update_stations(req, result):
            view.dismiss()
            json_data = json.loads(result)
            conn = sqlite3.connect(NAME_DATABASE)
            with conn:
                cur = conn.cursor()
                cur.executemany('INSERT OR REPLACE INTO estacion VALUES (?, ?);', json_data )
                cur.execute('SELECT * FROM estacion;')
                rows = cur.fetchall()
                if rows:
                    self.manager.get_screen("screen_list").ids.spinner_station.values = [nombre for _, nombre in rows]
            conn.close()
            modal_view_alert('Estaciones Actualizadas','Cerrar',
                Image(source=SOURCE_CHECK, size=(100,100)))

        def error_stations(req, error):
            view.dismiss()
            modal_view_alert('¡Error!','Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        def failure_stations(req, result):
            view.dismiss()
            modal_view_alert('Error de conexión...\nReintente mas tarde','Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        #self.manager.get_screen("screen_list").ids.spinner_station.values = ['Hola %i' % i for i in range(20)]
        params = urllib.parse.urlencode({'action': 'stations'})
        headers = {"Authorization": "Token {0}".format(app.api_token)}
        req = UrlRequest(URL_ENDPOINT+'?'+params, req_headers=headers,
            on_success=update_stations, on_progress=progress_stations,
        	on_error=error_stations, on_failure=failure_stations)

        view = ModalView(size_hint=(None, None), size=(400, 400))
        layout = GridLayout(cols=1, padding=10)

        content = Button(
            text="Cerrar", 
            size_hint=(None, None), 
            size=(380, 100),
            valign= 'center')
        label = Label(text="Esperando respuesta...")

        layout.add_widget(label)
        layout.add_widget(content)
        view.add_widget(layout)

        content.bind(on_press=view.dismiss)
        view.open()

        return view

    def syncron_colas(self):

        app = App.get_running_app()
        if not app.is_login:
            return modal_view_alert('No esta loggeado para \nhacer esta acción', 'Cerrar', 
                Image(source=SOURCE_FAIL, size=(100,100)))

        def progress_cola(request, current_size, total_size):
            label.text = "Cargando " + str(round(current_size*100/total_size)) + "%"

        def update_cola(req, result):
            view.dismiss()
            json_data = json.loads(result)
            #print(json_data)
            conn = sqlite3.connect(NAME_DATABASE)
            with conn:
                cur = conn.cursor()
                for obj in json_data:
                    cur.execute('INSERT INTO cola VALUES (NULL, "%s", "%s", "%s", %i, %i);' %\
                        (obj["estacion"], obj["placa"], obj["created_at"], False, True))
                cur.execute('INSERT INTO updates VALUES (NULL, "%s");' % self.date_update.isoformat())

            conn.close()
            modal_view_alert('Datos cargados','Cerrar',
                Image(source=SOURCE_CHECK, size=(100,100)))

        def error_cola(req, result):
            view.dismiss()
            modal_view_alert('¡Error!','Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        def failure_cola(req, result):
            view.dismiss()
            modal_view_alert('Error de conexión...\nReintente mas tarde','Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        self.date_update = datetime.now()
        params = urllib.parse.urlencode({'action':'update', 'date':(self.date_update-timedelta(days=DAYS_COUNT)).isoformat() })

        conn = sqlite3.connect(NAME_DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT id, update_date FROM updates ORDER BY Datetime(update_date) DESC LIMIT 1')
            rows = cur.fetchall()
            if rows:
                id_date, update_date = rows.pop()
                params = urllib.parse.urlencode({'action':'update', 'date': update_date})
        conn.close()

        headers = {"Authorization": "Token {0}".format(app.api_token)}

        req = UrlRequest(URL_ENDPOINT+'?'+params, req_headers= headers,
            on_success=update_cola, on_progress=progress_cola,
        	on_error=error_cola, on_failure=failure_cola)



        view = ModalView(size_hint=(None, None), size=(400, 400))
        layout = GridLayout(cols=1, padding=10)

        content = Button(
            text="Cerrar", 
            size_hint=(None, None), 
            size=(380, 100),
            valign= 'center')
        label = Label(text="Esperando respuesta...")

        layout.add_widget(label)
        layout.add_widget(content)
        view.add_widget(layout)

        content.bind(on_press=view.dismiss)
        view.open()

        return view

    def syncron_subir(self, wait=False):

        app = App.get_running_app()
        if not app.is_login:
            return modal_view_alert('No esta loggeado para \nhacer esta acción', 'Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        headers = {
        	'Content-type': 'application/json', 
        	"Authorization": "Token {0}".format(app.api_token)}

        def progress_subir(req, cs, ts):
            label.text = "Cargando " + str(round(cs*100/ts)) + "%"

        def update_subir(req, result):
            view.dismiss()
            conn = sqlite3.connect(NAME_DATABASE)
            with conn:
                cur = conn.cursor()
                cur.execute('UPDATE cola SET up = 1 WHERE up = 0;')
            conn.close()
            modal_view_alert('Datos cargados','Cerrar',
                Image(source=SOURCE_CHECK, size=(100,100)))

        def error_subir(req, result):
            view.dismiss()
            modal_view_alert('¡Error!','Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        def failure_subir(req, result):
            view.dismiss()
            modal_view_alert('Error de conexión...\nReintente mas tarde','Cerrar',
                Image(source=SOURCE_FAIL, size=(100,100)))

        view = ModalView(size_hint=(None, None), size=(400, 400))
        layout = GridLayout(cols=1, padding=10)

        content = Button(
            text="Cerrar", 
            size_hint=(None, None), 
            size=(380, 100),
            valign= 'center')
        label = Label(text="Esperando respuesta...")

        layout.add_widget(label)
        layout.add_widget(content)
        view.add_widget(layout)

        content.bind(on_press=view.dismiss)
        view.open()
        
        conn = sqlite3.connect(NAME_DATABASE)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT id, estacion, placa, created_at, estado FROM cola WHERE up = 0;')

            rows = cur.fetchall()
            if not rows:
                label.text = "No hay elementos a actualizar"
                return view

            data_body = json.dumps([{
                'ie': estacion,
                'pl': placa,
                'ca': created_at,
                'ir': estado
                } for _id, estacion, placa, created_at, estado in rows ])

            req = UrlRequest(URL_ENDPOINT, req_headers=headers, req_body=data_body,
                on_success=update_subir, on_progress=progress_subir,
                on_error=error_subir, on_failure=failure_subir)

            if wait:
                #while not req.is_finished:
                #    pass
                req.wait()

        conn.close()

        return view


class DemoApp(App):

    username = StringProperty(None)
    password = StringProperty(None)
    is_login = BooleanProperty(False)
    api_token = StringProperty(None)

    def build(self):
        self.title = 'Aplicación DGas'
        return Display()

    def get_application_config(self):
        if(not self.username):
            return super(DemoApp, self).get_application_config()

        conf_directory = self.user_data_dir + '/' + self.username

        if(not os.path.exists(conf_directory)):
            os.makedirs(conf_directory)

        return super(DemoApp, self).get_application_config(
            '%s/config.cfg' % (conf_directory)
        )

if __name__ == '__main__':
    DemoApp().run()
