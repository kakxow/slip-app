import datetime as dt
from string import ascii_uppercase

import factory

from db import Slip

start_date = dt.datetime(2019, 12, 1)
end_date = dt.datetime(2020, 2, 1)


class SlipFactory(factory.Factory):
    class Meta:
        model = Slip

    merchant_name = factory.Faker('text', max_nb_chars=100)
    city = factory.Faker('city')
    address = factory.Faker('address')
    phone_num = factory.Faker('msisdn')
    date = factory.Faker('date_between', start_date=start_date, end_date=end_date)
    time = factory.Faker('time_object')
    operation_type = factory.Faker('random_element', elements=('Refund', 'Payment'))
    pos_id = factory.Faker('numerify', text='########')
    merchant_num = factory.Faker('numerify', text='############')
    fin_service = factory.Faker('lexify')
    something = factory.Faker('lexify')
    card_number = factory.Faker('numerify', text='####')
    card_holder = factory.Faker('name')
    summ = factory.Faker('random_int', max=600000)
    result = 'Success'
    auth_code = factory.Faker('lexify', text='??????')
    ref_num = factory.Faker('numerify', text='############')
    payment_type = factory.Faker('text', max_nb_chars=50)
    object_code = factory.Faker('bothify', text='??##', letters=ascii_uppercase)
    updated = dt.datetime.today().date()

    @factory.lazy_attribute
    def file_link(self):
        return f'\\\\Msk-vm-slip\\SLIP\\{self.object_code}\\{self.date.year}\\{self.date.month}\\' \
            f'{self.object_code}{factory.Faker("numerify", text="#####################")}.pdf'


slip = {
    "address": "тестовый проезд, дом 19",
    "auth_code": "123321",
    "card_holder": "MAKSIM/SUKHANOV",
    "card_number": "1721",
    "city": "Тест",
    "date": "2020-02-06",
    "file_link": "\\\\Msk-vm-slip\\SLIP\\KG34\\2019\\01\\KG12345678998745632112365.pdf",
    "fin_service": "MasterCard",
    "merchant_name": "SET SVYAZNOY KG34",
    "merchant_num": "990000006829",
    "object_code": "KG34",
    "operation_type": "Оплата",
    "payment_type": "Введен ПИН-код",
    "phone_num": "4957870333",
    "pos_id": "00477484",
    "ref_num": "900186288187",
    "result": "ОДОБРЕНО",
    "summ": '1721.0',
    "time": "12:34",
    'updated': '2020-02-06',
}

slip2 = {
    **slip,
    "ref_num": "900186288188",
    "file_link": "\\\\Msk-vm-slip\\SLIP\\KG34\\2019\\01\\KG12345678998745632112368.pdf",
}
slip3 = {
    **slip,
    "ref_num": "900186288189",
    "file_link": "\\\\Msk-vm-slip\\SLIP\\KG34\\2019\\01\\KG12345678998745632112369.pdf",
}
slips = (slip, slip2, slip3)
